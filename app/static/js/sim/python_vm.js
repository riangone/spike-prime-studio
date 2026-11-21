/**
 * Lightweight, deterministic Python 3 / MicroPython-subset interpreter for SPIKE 3 programs.
 *
 * Features:
 *   - Indentation-aware lexer (INDENT/DEDENT, comments, multiline brackets, f-strings, triple quotes)
 *   - Recursive-descent AST parser (async def / await, chained comparisons, tuple unpacking,
 *     default/keyword args, global, slices, comprehensions, if/elif/else, while/for/break/continue)
 *   - Async evaluator running on a cooperative virtual clock with instant cancellation,
 *     line-number tracking, and infinite-loop throttling so browser UI never freezes.
 */

export const NATIVE_FN = Symbol('NativeFn');
export const PY_TUPLE = Symbol('PyTuple');

export function nativeFn(fn) {
  fn[NATIVE_FN] = true;
  return fn;
}

export function pyTuple(items) {
  const arr = Array.from(items);
  arr[PY_TUPLE] = true;
  return arr;
}

export function pyAwaitable(promise) {
  // Suppress unhandled rejection if caller uses fire-and-forget and simulation stops later,
  // while `await val.start()` still observes the original promise's rejection.
  promise.catch(() => {});
  return { __pyCoro: true, start: () => promise };
}

export class SimCancelledError extends Error {
  constructor() {
    super('Simulation stopped');
    this.name = 'SimCancelledError';
  }
}

export class PyError extends Error {
  constructor(type, message, line = null) {
    super(line ? `${type} (line ${line}): ${message}` : `${type}: ${message}`);
    this.name = 'PyError';
    this.pyType = type;
    this.line = line;
  }
}

class ReturnSignal {
  constructor(value) { this.value = value; }
}
class BreakSignal {}
class ContinueSignal {}

// =================================================================================================
// 1. Lexer
// =================================================================================================
const KEYWORDS = new Set([
  'False', 'None', 'True', 'and', 'as', 'async', 'await', 'break', 'continue',
  'def', 'elif', 'else', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
  'lambda', 'nonlocal', 'not', 'or', 'pass', 'return', 'while',
]);

const TWO_CHAR_OPS = new Set([
  '==', '!=', '<=', '>=', '//', '**', '+=', '-=', '*=', '/=', '%=', '<<', '>>', '->',
]);
const THREE_CHAR_OPS = new Set(['//=', '**=', '<<=', '>>=']);

export function tokenize(source) {
  const src = source.replace(/\r\n?/g, '\n');
  const tokens = [];
  const indentStack = [0];
  let i = 0;
  let line = 1;
  let parenDepth = 0;
  let atLineStart = true;

  const push = (type, value, ln = line) => tokens.push({ type, value, line: ln });

  while (i < src.length) {
    if (atLineStart && parenDepth === 0) {
      // Measure leading spaces/tabs; skip blank & comment-only lines
      let j = i;
      let col = 0;
      while (j < src.length && (src[j] === ' ' || src[j] === '\t')) {
        col += src[j] === '\t' ? 4 : 1;
        j++;
      }
      if (j >= src.length) {
        i = j;
        break;
      }
      if (src[j] === '\n') {
        i = j + 1;
        line++;
        continue;
      }
      if (src[j] === '#') {
        while (j < src.length && src[j] !== '\n') j++;
        if (j < src.length) { j++; line++; }
        i = j;
        continue;
      }
      i = j;
      atLineStart = false;
      const top = indentStack[indentStack.length - 1];
      if (col > top) {
        indentStack.push(col);
        push('INDENT', col);
      } else if (col < top) {
        while (indentStack.length > 1 && indentStack[indentStack.length - 1] > col) {
          indentStack.pop();
          push('DEDENT', col);
        }
        if (indentStack[indentStack.length - 1] !== col) {
          throw new PyError('IndentationError', 'unindent does not match any outer indentation level', line);
        }
      }
    }

    const ch = src[i];

    // Whitespace within line
    if (ch === ' ' || ch === '\t') { i++; continue; }

    // Line continuation backslash
    if (ch === '\\' && src[i + 1] === '\n') { i += 2; line++; continue; }

    // Comment
    if (ch === '#') {
      while (i < src.length && src[i] !== '\n') i++;
      continue;
    }

    // Newline
    if (ch === '\n') {
      i++;
      if (parenDepth === 0) {
        if (tokens.length > 0 && tokens[tokens.length - 1].type !== 'NEWLINE' && tokens[tokens.length - 1].type !== 'INDENT') {
          push('NEWLINE', '\n', line);
        }
        atLineStart = true;
      }
      line++;
      continue;
    }

    // String / f-string literals
    const isFString = (ch === 'f' || ch === 'F') && (src[i + 1] === '"' || src[i + 1] === "'");
    const isRawString = (ch === 'r' || ch === 'R') && (src[i + 1] === '"' || src[i + 1] === "'");
    if (ch === '"' || ch === "'" || isFString || isRawString) {
      const startLine = line;
      const prefix = isFString ? 'f' : isRawString ? 'r' : '';
      if (prefix) i++;
      const quote = src[i];
      const triple = src.slice(i, i + 3) === quote.repeat(3);
      i += triple ? 3 : 1;
      let val = '';
      let closed = false;
      while (i < src.length) {
        if (triple && src.slice(i, i + 3) === quote.repeat(3)) {
          i += 3;
          closed = true;
          break;
        }
        if (!triple && src[i] === quote) {
          i++;
          closed = true;
          break;
        }
        if (src[i] === '\n') {
          if (!triple) throw new PyError('SyntaxError', 'unterminated string literal', startLine);
          val += '\n';
          i++;
          line++;
          continue;
        }
        if (src[i] === '\\' && prefix !== 'r' && i + 1 < src.length) {
          const nxt = src[i + 1];
          if (nxt === 'n') val += '\n';
          else if (nxt === 't') val += '\t';
          else if (nxt === 'r') val += '\r';
          else if (nxt === '\\') val += '\\';
          else if (nxt === "'") val += "'";
          else if (nxt === '"') val += '"';
          else val += '\\' + nxt;
          i += 2;
        } else {
          val += src[i++];
        }
      }
      if (!closed) throw new PyError('SyntaxError', 'unterminated string literal', startLine);
      push(prefix === 'f' ? 'FSTRING' : 'STRING', val, startLine);
      continue;
    }

    // Numbers
    if ((ch >= '0' && ch <= '9') || (ch === '.' && src[i + 1] >= '0' && src[i + 1] <= '9')) {
      const start = i;
      if (ch === '0' && (src[i + 1] === 'x' || src[i + 1] === 'X')) {
        i += 2;
        while (i < src.length && /[0-9a-fA-F_]/.test(src[i])) i++;
        push('NUMBER', parseInt(src.slice(start + 2, i).replace(/_/g, ''), 16));
        continue;
      }
      if (ch === '0' && (src[i + 1] === 'b' || src[i + 1] === 'B')) {
        i += 2;
        while (i < src.length && /[01_]/.test(src[i])) i++;
        push('NUMBER', parseInt(src.slice(start + 2, i).replace(/_/g, ''), 2));
        continue;
      }
      let isFloat = false;
      while (i < src.length && /[0-9_]/.test(src[i])) i++;
      if (src[i] === '.' && src[i + 1] !== '.') {
        isFloat = true;
        i++;
        while (i < src.length && /[0-9_]/.test(src[i])) i++;
      }
      if (src[i] === 'e' || src[i] === 'E') {
        isFloat = true;
        i++;
        if (src[i] === '+' || src[i] === '-') i++;
        while (i < src.length && /[0-9_]/.test(src[i])) i++;
      }
      const raw = src.slice(start, i).replace(/_/g, '');
      push('NUMBER', isFloat ? parseFloat(raw) : parseInt(raw, 10));
      continue;
    }

    // Identifiers & keywords
    if (/[A-Za-z_\u00C0-\uFFFF]/.test(ch)) {
      const start = i;
      while (i < src.length && /[A-Za-z0-9_\u00C0-\uFFFF]/.test(src[i])) i++;
      const word = src.slice(start, i);
      push(KEYWORDS.has(word) ? 'KW' : 'NAME', word);
      continue;
    }

    // Operators & punctuation
    const three = src.slice(i, i + 3);
    if (THREE_CHAR_OPS.has(three)) { push('OP', three); i += 3; continue; }
    const two = src.slice(i, i + 2);
    if (TWO_CHAR_OPS.has(two)) { push('OP', two); i += 2; continue; }

    if (ch === '(' || ch === '[' || ch === '{') { parenDepth++; push('OP', ch); i++; continue; }
    if (ch === ')' || ch === ']' || ch === '}') { parenDepth = Math.max(0, parenDepth - 1); push('OP', ch); i++; continue; }
    if ('+-*/%=<>!.,:;@&|^~'.includes(ch)) { push('OP', ch); i++; continue; }

    throw new PyError('SyntaxError', `unexpected character '${ch}'`, line);
  }

  if (tokens.length > 0 && tokens[tokens.length - 1].type !== 'NEWLINE') {
    push('NEWLINE', '\n', line);
  }
  while (indentStack.length > 1) {
    indentStack.pop();
    push('DEDENT', 0, line);
  }
  push('EOF', '', line);
  return tokens;
}

// =================================================================================================
// 2. Recursive-Descent Parser
// =================================================================================================
export function parse(source) {
  const tokens = tokenize(source);
  let pos = 0;

  const peek = (off = 0) => tokens[Math.min(pos + off, tokens.length - 1)];
  const next = () => tokens[pos++];
  const at = (type, value = null) => {
    const t = peek();
    return t.type === type && (value === null || t.value === value);
  };
  const match = (type, value = null) => {
    if (at(type, value)) return next();
    return null;
  };
  const expect = (type, value = null) => {
    const t = peek();
    if (t.type === type && (value === null || t.value === value)) return next();
    throw new PyError('SyntaxError', `expected ${value || type}, got '${t.value || t.type}'`, t.line);
  };
  const skipNewlines = () => { while (match('NEWLINE')) {} };

  function parseModule() {
    const body = [];
    skipNewlines();
    while (!at('EOF')) {
      body.push(...parseStatement());
      skipNewlines();
    }
    return { kind: 'Module', body };
  }

  function parseBlock() {
    expect('OP', ':');
    if (match('NEWLINE')) {
      skipNewlines();
      expect('INDENT');
      const stmts = [];
      skipNewlines();
      while (!at('DEDENT') && !at('EOF')) {
        stmts.push(...parseStatement());
        skipNewlines();
      }
      expect('DEDENT');
      return stmts;
    }
    return parseSimpleLine();
  }

  function parseStatement() {
    const t = peek();
    if (t.type === 'KW') {
      if (t.value === 'if') return [parseIf()];
      if (t.value === 'while') return [parseWhile()];
      if (t.value === 'for') return [parseFor()];
      if (t.value === 'def') return [parseDef(false)];
      if (t.value === 'async') {
        next();
        if (at('KW', 'def')) return [parseDef(true)];
        throw new PyError('SyntaxError', 'expected def after async', peek().line);
      }
    }
    return parseSimpleLine();
  }

  function parseSimpleLine() {
    const stmts = [parseSimpleStmt()];
    while (match('OP', ';')) {
      if (at('NEWLINE') || at('EOF')) break;
      stmts.push(parseSimpleStmt());
    }
    if (!at('EOF') && !at('DEDENT')) expect('NEWLINE');
    return stmts;
  }

  function parseSimpleStmt() {
    const t = peek();
    if (t.type === 'KW') {
      if (t.value === 'pass') { next(); return { kind: 'Pass', line: t.line }; }
      if (t.value === 'break') { next(); return { kind: 'Break', line: t.line }; }
      if (t.value === 'continue') { next(); return { kind: 'Continue', line: t.line }; }
      if (t.value === 'return') {
        next();
        const value = (at('NEWLINE') || at('OP', ';') || at('EOF')) ? null : parseExprList();
        return { kind: 'Return', value, line: t.line };
      }
      if (t.value === 'global' || t.value === 'nonlocal') {
        const kw = next().value;
        const names = [expect('NAME').value];
        while (match('OP', ',')) names.push(expect('NAME').value);
        return { kind: kw === 'global' ? 'Global' : 'Nonlocal', names, line: t.line };
      }
      if (t.value === 'import') return parseImport();
      if (t.value === 'from') return parseFromImport();
    }

    const expr = parseExprList();
    const op = peek();
    if (op.type === 'OP' && op.value === '=') {
      next();
      const val = parseExprList();
      return { kind: 'Assign', target: expr, value: val, line: t.line };
    }
    if (op.type === 'OP' && ['+=', '-=', '*=', '/=', '//=', '%=', '**='].includes(op.value)) {
      next();
      const val = parseExpr();
      return { kind: 'AugAssign', target: expr, op: op.value.slice(0, -1), value: val, line: t.line };
    }
    return { kind: 'ExprStmt', expr, line: t.line };
  }

  function parseImport() {
    const ln = expect('KW', 'import').line;
    const names = [];
    do {
      let mod = expect('NAME').value;
      while (match('OP', '.')) mod += '.' + expect('NAME').value;
      const alias = match('KW', 'as') ? expect('NAME').value : null;
      names.push({ mod, alias: alias || mod.split('.')[0] });
    } while (match('OP', ','));
    return { kind: 'Import', names, line: ln };
  }

  function parseFromImport() {
    const ln = expect('KW', 'from').line;
    let mod = expect('NAME').value;
    while (match('OP', '.')) mod += '.' + expect('NAME').value;
    expect('KW', 'import');
    const parens = !!match('OP', '(');
    const items = [];
    do {
      if (parens && at('OP', ')')) break;
      const name = expect('NAME').value;
      const alias = match('KW', 'as') ? expect('NAME').value : name;
      items.push({ name, alias });
    } while (match('OP', ','));
    if (parens) expect('OP', ')');
    return { kind: 'FromImport', mod, items, line: ln };
  }

  function parseIf() {
    const ln = expect('KW', 'if').line;
    const test = parseExpr();
    const body = parseBlock();
    const elifs = [];
    skipNewlines();
    while (at('KW', 'elif')) {
      const eln = next().line;
      const etest = parseExpr();
      const ebody = parseBlock();
      elifs.push({ test: etest, body: ebody, line: eln });
      skipNewlines();
    }
    let orelse = [];
    if (match('KW', 'else')) {
      orelse = parseBlock();
    }
    return { kind: 'If', test, body, elifs, orelse, line: ln };
  }

  function parseWhile() {
    const ln = expect('KW', 'while').line;
    const test = parseExpr();
    const body = parseBlock();
    return { kind: 'While', test, body, line: ln };
  }

  function parseFor() {
    const ln = expect('KW', 'for').line;
    const target = parseTargetList();
    expect('KW', 'in');
    const iter = parseExprList();
    const body = parseBlock();
    return { kind: 'For', target, iter, body, line: ln };
  }

  function parseTargetList() {
    const first = parsePrimary();
    if (!at('OP', ',')) return first;
    const items = [first];
    while (match('OP', ',')) {
      if (at('KW', 'in')) break;
      items.push(parsePrimary());
    }
    return { kind: 'Tuple', items, line: first.line };
  }

  function parseDef(isAsync) {
    const ln = expect('KW', 'def').line;
    const name = expect('NAME').value;
    expect('OP', '(');
    const params = [];
    while (!at('OP', ')')) {
      const pname = expect('NAME').value;
      // Optional type annotation
      if (match('OP', ':')) parseExpr();
      let defVal = null;
      if (match('OP', '=')) defVal = parseExpr();
      params.push({ name: pname, defaultVal: defVal });
      if (!match('OP', ',')) break;
    }
    expect('OP', ')');
    if (match('OP', '->')) parseExpr();
    const body = parseBlock();
    return { kind: 'FuncDef', isAsync, name, params, body, line: ln };
  }

  function parseExprList() {
    const first = parseExpr();
    if (!at('OP', ',')) return first;
    const items = [first];
    while (match('OP', ',')) {
      if (at('NEWLINE') || at('OP', '=') || at('OP', ';') || at('OP', ')') || at('OP', ']') || at('EOF')) break;
      items.push(parseExpr());
    }
    return { kind: 'Tuple', items, line: first.line };
  }

  function parseExpr() {
    if (at('KW', 'lambda')) {
      const ln = next().line;
      const params = [];
      if (!at('OP', ':')) {
        do {
          const pname = expect('NAME').value;
          const defVal = match('OP', '=') ? parseExpr() : null;
          params.push({ name: pname, defaultVal: defVal });
        } while (match('OP', ','));
      }
      expect('OP', ':');
      const body = parseExpr();
      return { kind: 'Lambda', params, body, line: ln };
    }
    const expr = parseOr();
    if (match('KW', 'if')) {
      const cond = parseOr();
      expect('KW', 'else');
      const orelse = parseExpr();
      return { kind: 'Ternary', test: cond, body: expr, orelse, line: expr.line };
    }
    return expr;
  }

  function parseOr() {
    let left = parseAnd();
    while (match('KW', 'or')) {
      const right = parseAnd();
      left = { kind: 'BoolOp', op: 'or', left, right, line: left.line };
    }
    return left;
  }

  function parseAnd() {
    let left = parseNot();
    while (match('KW', 'and')) {
      const right = parseNot();
      left = { kind: 'BoolOp', op: 'and', left, right, line: left.line };
    }
    return left;
  }

  function parseNot() {
    if (at('KW', 'not')) {
      const ln = next().line;
      return { kind: 'UnaryOp', op: 'not', operand: parseNot(), line: ln };
    }
    return parseComparison();
  }

  function parseComparison() {
    const left = parseBitOr();
    const ops = [];
    const comparators = [];
    while (true) {
      let op = null;
      const t = peek();
      if (t.type === 'OP' && ['<', '<=', '>', '>=', '==', '!='].includes(t.value)) {
        op = next().value;
      } else if (t.type === 'KW' && t.value === 'in') {
        next(); op = 'in';
      } else if (t.type === 'KW' && t.value === 'not' && peek(1).type === 'KW' && peek(1).value === 'in') {
        next(); next(); op = 'not in';
      } else if (t.type === 'KW' && t.value === 'is') {
        next();
        if (match('KW', 'not')) op = 'is not';
        else op = 'is';
      }
      if (!op) break;
      ops.push(op);
      comparators.push(parseBitOr());
    }
    if (ops.length === 0) return left;
    return { kind: 'Compare', left, ops, comparators, line: left.line };
  }

  function parseBitOr() {
    let left = parseBitXor();
    while (match('OP', '|')) left = { kind: 'BinOp', op: '|', left, right: parseBitXor(), line: left.line };
    return left;
  }

  function parseBitXor() {
    let left = parseBitAnd();
    while (match('OP', '^')) left = { kind: 'BinOp', op: '^', left, right: parseBitAnd(), line: left.line };
    return left;
  }

  function parseBitAnd() {
    let left = parseShift();
    while (match('OP', '&')) left = { kind: 'BinOp', op: '&', left, right: parseShift(), line: left.line };
    return left;
  }

  function parseShift() {
    let left = parseAdd();
    while (at('OP', '<<') || at('OP', '>>')) {
      const op = next().value;
      left = { kind: 'BinOp', op, left, right: parseAdd(), line: left.line };
    }
    return left;
  }

  function parseAdd() {
    let left = parseMul();
    while (at('OP', '+') || at('OP', '-')) {
      const op = next().value;
      left = { kind: 'BinOp', op, left, right: parseMul(), line: left.line };
    }
    return left;
  }

  function parseMul() {
    let left = parseUnary();
    while (at('OP', '*') || at('OP', '/') || at('OP', '//') || at('OP', '%')) {
      const op = next().value;
      left = { kind: 'BinOp', op, left, right: parseUnary(), line: left.line };
    }
    return left;
  }

  function parseUnary() {
    if (at('OP', '-') || at('OP', '+') || at('OP', '~')) {
      const t = next();
      return { kind: 'UnaryOp', op: t.value, operand: parseUnary(), line: t.line };
    }
    return parsePower();
  }

  function parsePower() {
    const left = parseAwait();
    if (match('OP', '**')) {
      return { kind: 'BinOp', op: '**', left, right: parseUnary(), line: left.line };
    }
    return left;
  }

  function parseAwait() {
    if (at('KW', 'await')) {
      const ln = next().line;
      return { kind: 'Await', value: parsePrimary(), line: ln };
    }
    return parsePrimary();
  }

  function parsePrimary() {
    let node = parseAtom();
    while (true) {
      if (match('OP', '.')) {
        const attr = expect('NAME').value;
        node = { kind: 'Attr', obj: node, attr, line: node.line };
      } else if (match('OP', '(')) {
        const args = [];
        const kwargs = [];
        while (!at('OP', ')')) {
          if (peek().type === 'NAME' && peek(1).type === 'OP' && peek(1).value === '=') {
            const k = next().value;
            next(); // '='
            kwargs.push({ key: k, value: parseExpr() });
          } else {
            args.push(parseExpr());
          }
          if (!match('OP', ',')) break;
        }
        expect('OP', ')');
        node = { kind: 'Call', func: node, args, kwargs, line: node.line };
      } else if (match('OP', '[')) {
        // Index or slice a[start:stop:step]
        let lower = null;
        let upper = null;
        let step = null;
        let isSlice = false;
        if (!at('OP', ':')) lower = parseExpr();
        if (match('OP', ':')) {
          isSlice = true;
          if (!at('OP', ':') && !at('OP', ']')) upper = parseExpr();
          if (match('OP', ':') && !at('OP', ']')) step = parseExpr();
        }
        expect('OP', ']');
        node = isSlice
          ? { kind: 'Slice', obj: node, lower, upper, step, line: node.line }
          : { kind: 'Subscript', obj: node, index: lower, line: node.line };
      } else {
        break;
      }
    }
    return node;
  }

  function parseAtom() {
    const t = peek();
    if (t.type === 'NUMBER') { next(); return { kind: 'Literal', value: t.value, line: t.line }; }
    if (t.type === 'STRING') {
      let s = next().value;
      while (at('STRING')) s += next().value; // implicit adjacent string concat
      return { kind: 'Literal', value: s, line: t.line };
    }
    if (t.type === 'FSTRING') { next(); return { kind: 'FString', raw: t.value, line: t.line }; }
    if (t.type === 'KW' && t.value === 'True') { next(); return { kind: 'Literal', value: true, line: t.line }; }
    if (t.type === 'KW' && t.value === 'False') { next(); return { kind: 'Literal', value: false, line: t.line }; }
    if (t.type === 'KW' && t.value === 'None') { next(); return { kind: 'Literal', value: null, line: t.line }; }
    if (t.type === 'NAME') { next(); return { kind: 'Name', id: t.value, line: t.line }; }

    if (match('OP', '(')) {
      if (match('OP', ')')) return { kind: 'Tuple', items: [], line: t.line };
      const first = parseExpr();
      if (match('OP', ',')) {
        const items = [first];
        while (!at('OP', ')')) {
          items.push(parseExpr());
          if (!match('OP', ',')) break;
        }
        expect('OP', ')');
        return { kind: 'Tuple', items, line: t.line };
      }
      expect('OP', ')');
      return first;
    }

    if (match('OP', '[')) {
      if (match('OP', ']')) return { kind: 'List', items: [], line: t.line };
      const first = parseExpr();
      if (match('KW', 'for')) {
        const target = parseTargetList();
        expect('KW', 'in');
        const iter = parseOr();
        const cond = match('KW', 'if') ? parseOr() : null;
        expect('OP', ']');
        return { kind: 'ListComp', elt: first, target, iter, cond, line: t.line };
      }
      const items = [first];
      while (match('OP', ',')) {
        if (at('OP', ']')) break;
        items.push(parseExpr());
      }
      expect('OP', ']');
      return { kind: 'List', items, line: t.line };
    }

    if (match('OP', '{')) {
      const entries = [];
      while (!at('OP', '}')) {
        const key = parseExpr();
        expect('OP', ':');
        const val = parseExpr();
        entries.push({ key, val });
        if (!match('OP', ',')) break;
      }
      expect('OP', '}');
      return { kind: 'Dict', entries, line: t.line };
    }

    throw new PyError('SyntaxError', `unexpected token '${t.value || t.type}'`, t.line);
  }

  return parseModule();
}

// =================================================================================================
// 3. Python Semantics Helpers
// =================================================================================================
export function pyTruthy(v) {
  if (v === null || v === undefined || v === false || v === 0 || v === '') return false;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === 'object' && v.constructor === Object) return Object.keys(v).length > 0;
  return true;
}

export function pyEq(a, b) {
  if (a === b) return true;
  if (typeof a === 'boolean' && typeof b === 'number') return Number(a) === b;
  if (typeof a === 'number' && typeof b === 'boolean') return a === Number(b);
  if (Array.isArray(a) && Array.isArray(b)) {
    if (!!a[PY_TUPLE] !== !!b[PY_TUPLE] || a.length !== b.length) return false;
    return a.every((x, i) => pyEq(x, b[i]));
  }
  return false;
}

export function pyStr(v) {
  if (v === null || v === undefined) return 'None';
  if (v === true) return 'True';
  if (v === false) return 'False';
  if (Array.isArray(v)) {
    const inner = v.map(pyRepr).join(', ');
    if (v[PY_TUPLE]) return v.length === 1 ? `(${inner},)` : `(${inner})`;
    return `[${inner}]`;
  }
  if (typeof v === 'object' && v.constructor === Object) {
    return '{' + Object.entries(v).map(([k, val]) => `${pyRepr(k)}: ${pyRepr(val)}`).join(', ') + '}';
  }
  return String(v);
}

function pyRepr(v) {
  if (typeof v === 'string') return `'${v}'`;
  return pyStr(v);
}

function pyNum(v, line) {
  if (typeof v === 'number') return v;
  if (typeof v === 'boolean') return v ? 1 : 0;
  throw new PyError('TypeError', `expected number, got ${typeof v}`, line);
}

function pyBinOp(op, a, b, line) {
  switch (op) {
    case '+':
      if (typeof a === 'string' && typeof b === 'string') return a + b;
      if (Array.isArray(a) && Array.isArray(b)) return a.concat(b);
      return pyNum(a, line) + pyNum(b, line);
    case '-': return pyNum(a, line) - pyNum(b, line);
    case '*':
      if (typeof a === 'string' && typeof b === 'number') return a.repeat(Math.max(0, Math.trunc(b)));
      if (typeof b === 'string' && typeof a === 'number') return b.repeat(Math.max(0, Math.trunc(a)));
      if (Array.isArray(a) && typeof b === 'number') {
        const res = [];
        for (let k = 0; k < Math.max(0, Math.trunc(b)); k++) res.push(...a);
        return res;
      }
      return pyNum(a, line) * pyNum(b, line);
    case '/': {
      const den = pyNum(b, line);
      if (den === 0) throw new PyError('ZeroDivisionError', 'division by zero', line);
      return pyNum(a, line) / den;
    }
    case '//': {
      const den = pyNum(b, line);
      if (den === 0) throw new PyError('ZeroDivisionError', 'integer division or modulo by zero', line);
      return Math.floor(pyNum(a, line) / den);
    }
    case '%': {
      const den = pyNum(b, line);
      if (den === 0) throw new PyError('ZeroDivisionError', 'integer division or modulo by zero', line);
      const num = pyNum(a, line);
      return ((num % den) + den) % den;
    }
    case '**': return Math.pow(pyNum(a, line), pyNum(b, line));
    case '|': return Math.trunc(pyNum(a, line)) | Math.trunc(pyNum(b, line));
    case '^': return Math.trunc(pyNum(a, line)) ^ Math.trunc(pyNum(b, line));
    case '&': return Math.trunc(pyNum(a, line)) & Math.trunc(pyNum(b, line));
    case '<<': return Math.trunc(pyNum(a, line)) << Math.trunc(pyNum(b, line));
    case '>>': return Math.trunc(pyNum(a, line)) >> Math.trunc(pyNum(b, line));
    default: throw new PyError('SyntaxError', `unsupported operator ${op}`, line);
  }
}

function pyCompareOp(op, a, b) {
  const na = typeof a === 'boolean' ? Number(a) : a;
  const nb = typeof b === 'boolean' ? Number(b) : b;
  switch (op) {
    case '==': return pyEq(a, b);
    case '!=': return !pyEq(a, b);
    case '<': return na < nb;
    case '<=': return na <= nb;
    case '>': return na > nb;
    case '>=': return na >= nb;
    case 'is': return a === b;
    case 'is not': return a !== b;
    case 'in':
      if (typeof b === 'string') return b.includes(String(a));
      if (Array.isArray(b)) return b.some((x) => pyEq(x, a));
      if (b && typeof b === 'object') return Object.prototype.hasOwnProperty.call(b, String(a));
      return false;
    case 'not in': return !pyCompareOp('in', a, b);
    default: return false;
  }
}

function toIterable(val, line) {
  if (Array.isArray(val)) return val;
  if (typeof val === 'string') return Array.from(val);
  if (val && typeof val === 'object' && val.constructor === Object) return Object.keys(val);
  throw new PyError('TypeError', `'${typeof val}' object is not iterable`, line);
}

// =================================================================================================
// 4. Environment & Async Evaluator
// =================================================================================================
class Env {
  constructor(parent = null, globals = null) {
    this.vars = Object.create(null);
    this.parent = parent;
    this.globals = globals || this;
    this.globalNames = new Set();
  }
  get(name, line) {
    if (this.globalNames.has(name)) {
      if (name in this.globals.vars) return this.globals.vars[name];
      throw new PyError('NameError', `name '${name}' is not defined`, line);
    }
    let cur = this;
    while (cur) {
      if (name in cur.vars) return cur.vars[name];
      cur = cur.parent;
    }
    throw new PyError('NameError', `name '${name}' is not defined`, line);
  }
  set(name, val) {
    if (this.globalNames.has(name)) {
      this.globals.vars[name] = val;
    } else {
      this.vars[name] = val;
    }
  }
}

export class PythonVM {
  constructor({ modules = {}, onPrint = () => {}, onLine = () => {}, yieldTick = null, isCancelled = () => false } = {}) {
    this.modules = { ...this._stdlibModules(), ...modules };
    this.onPrint = onPrint;
    this.onLine = onLine;
    this.yieldTick = yieldTick;
    this.isCancelled = isCancelled;
    this.opBudget = 0;
    this.maxOpsPerTick = 4000;
  }

  _stdlibModules() {
    const mathMod = {
      pi: Math.PI,
      e: Math.E,
      tau: Math.PI * 2,
      sin: nativeFn(([x]) => Math.sin(x)),
      cos: nativeFn(([x]) => Math.cos(x)),
      tan: nativeFn(([x]) => Math.tan(x)),
      asin: nativeFn(([x]) => Math.asin(x)),
      acos: nativeFn(([x]) => Math.acos(x)),
      atan: nativeFn(([x]) => Math.atan(x)),
      atan2: nativeFn(([y, x]) => Math.atan2(y, x)),
      sqrt: nativeFn(([x]) => Math.sqrt(x)),
      fabs: nativeFn(([x]) => Math.abs(x)),
      floor: nativeFn(([x]) => Math.floor(x)),
      ceil: nativeFn(([x]) => Math.ceil(x)),
      radians: nativeFn(([x]) => (x * Math.PI) / 180),
      degrees: nativeFn(([x]) => (x * 180) / Math.PI),
      hypot: nativeFn((args) => Math.hypot(...args)),
      pow: nativeFn(([x, y]) => Math.pow(x, y)),
    };
    const randomMod = {
      random: nativeFn(() => Math.random()),
      randint: nativeFn(([a, b]) => Math.floor(Math.random() * (b - a + 1)) + a),
      uniform: nativeFn(([a, b]) => a + Math.random() * (b - a)),
      choice: nativeFn(([seq]) => seq[Math.floor(Math.random() * seq.length)]),
    };
    return { math: mathMod, random: randomMod };
  }

  _createBuiltins() {
    const self = this;
    return {
      print: nativeFn((args, kw) => {
        const sep = kw.sep !== undefined ? String(kw.sep) : ' ';
        self.onPrint(args.map(pyStr).join(sep));
        return null;
      }),
      range: nativeFn((args) => {
        let start = 0;
        let stop = 0;
        let step = 1;
        if (args.length === 1) stop = Math.trunc(args[0]);
        else if (args.length === 2) { start = Math.trunc(args[0]); stop = Math.trunc(args[1]); }
        else { start = Math.trunc(args[0]); stop = Math.trunc(args[1]); step = Math.trunc(args[2]); }
        if (step === 0) throw new PyError('ValueError', 'range() arg 3 must not be zero');
        const out = [];
        if (step > 0) for (let k = start; k < stop; k += step) out.push(k);
        else for (let k = start; k > stop; k += step) out.push(k);
        return out;
      }),
      len: nativeFn(([x]) => {
        if (typeof x === 'string' || Array.isArray(x)) return x.length;
        if (x && typeof x === 'object') return Object.keys(x).length;
        throw new PyError('TypeError', `object of type '${typeof x}' has no len()`);
      }),
      abs: nativeFn(([x]) => Math.abs(pyNum(x))),
      min: nativeFn((args) => {
        const arr = args.length === 1 && Array.isArray(args[0]) ? args[0] : args;
        return arr.reduce((m, v) => (v < m ? v : m));
      }),
      max: nativeFn((args) => {
        const arr = args.length === 1 && Array.isArray(args[0]) ? args[0] : args;
        return arr.reduce((m, v) => (v > m ? v : m));
      }),
      int: nativeFn(([x, base]) => {
        if (x === undefined) return 0;
        if (typeof x === 'boolean') return x ? 1 : 0;
        if (typeof x === 'number') return Math.trunc(x);
        const parsed = parseInt(String(x).trim(), base || 10);
        if (Number.isNaN(parsed)) throw new PyError('ValueError', `invalid literal for int(): '${x}'`);
        return parsed;
      }),
      float: nativeFn(([x]) => (x === undefined ? 0.0 : Number(x))),
      str: nativeFn(([x]) => (x === undefined ? '' : pyStr(x))),
      bool: nativeFn(([x]) => pyTruthy(x)),
      round: nativeFn(([x, n]) => {
        if (n === undefined) return Math.round(x);
        const f = Math.pow(10, n);
        return Math.round(x * f) / f;
      }),
      sum: nativeFn(([arr, start = 0]) => toIterable(arr).reduce((a, b) => a + b, start)),
      list: nativeFn(([x]) => (x === undefined ? [] : Array.from(toIterable(x)))),
      tuple: nativeFn(([x]) => pyTuple(x === undefined ? [] : toIterable(x))),
      dict: nativeFn((args, kw) => ({ ...kw })),
      enumerate: nativeFn(([seq, start = 0]) => toIterable(seq).map((v, idx) => pyTuple([start + idx, v]))),
      zip: nativeFn((seqs) => {
        const arrs = seqs.map((s) => toIterable(s));
        const n = arrs.length ? Math.min(...arrs.map((a) => a.length)) : 0;
        const out = [];
        for (let k = 0; k < n; k++) out.push(pyTuple(arrs.map((a) => a[k])));
        return out;
      }),
      sorted: nativeFn(([seq], kw) => {
        const arr = Array.from(toIterable(seq)).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
        return kw.reverse ? arr.reverse() : arr;
      }),
      reversed: nativeFn(([seq]) => Array.from(toIterable(seq)).reverse()),
      pow: nativeFn(([a, b]) => Math.pow(a, b)),
      chr: nativeFn(([n]) => String.fromCharCode(n)),
      ord: nativeFn(([s]) => String(s).charCodeAt(0)),
    };
  }

  async _checkTick() {
    if (this.isCancelled()) throw new SimCancelledError();
    this.opBudget++;
    if (this.opBudget >= this.maxOpsPerTick) {
      this.opBudget = 0;
      if (this.yieldTick) await this.yieldTick();
      if (this.isCancelled()) throw new SimCancelledError();
    }
  }

  async run(source) {
    const ast = parse(source);
    const rootEnv = new Env(null);
    Object.assign(rootEnv.vars, this._createBuiltins());
    await this._execBlock(ast.body, rootEnv);
  }

  async _execBlock(stmts, env) {
    for (const stmt of stmts) {
      await this._checkTick();
      const sig = await this._execStmt(stmt, env);
      if (sig) return sig;
    }
    return null;
  }

  async _execStmt(stmt, env) {
    if (stmt.line) this.onLine(stmt.line);
    switch (stmt.kind) {
      case 'Pass': return null;
      case 'Break': return new BreakSignal();
      case 'Continue': return new ContinueSignal();
      case 'Return': {
        const val = stmt.value ? await this._evalExpr(stmt.value, env) : null;
        return new ReturnSignal(val);
      }
      case 'Global':
        for (const n of stmt.names) env.globalNames.add(n);
        return null;
      case 'Nonlocal':
        return null;
      case 'Import': {
        for (const { mod, alias } of stmt.names) {
          const m = this.modules[mod];
          if (!m) throw new PyError('ModuleNotFoundError', `No module named '${mod}'`, stmt.line);
          env.set(alias, m);
        }
        return null;
      }
      case 'FromImport': {
        const m = this.modules[stmt.mod];
        if (!m) throw new PyError('ModuleNotFoundError', `No module named '${stmt.mod}'`, stmt.line);
        for (const { name, alias } of stmt.items) {
          if (!(name in m)) throw new PyError('ImportError', `cannot import name '${name}' from '${stmt.mod}'`, stmt.line);
          env.set(alias, m[name]);
        }
        return null;
      }
      case 'ExprStmt':
        await this._evalExpr(stmt.expr, env);
        return null;
      case 'Assign': {
        const val = await this._evalExpr(stmt.value, env);
        await this._assignTarget(stmt.target, val, env);
        return null;
      }
      case 'AugAssign': {
        const cur = await this._evalExpr(stmt.target, env);
        const rhs = await this._evalExpr(stmt.value, env);
        const nextVal = pyBinOp(stmt.op, cur, rhs, stmt.line);
        await this._assignTarget(stmt.target, nextVal, env);
        return null;
      }
      case 'If': {
        if (pyTruthy(await this._evalExpr(stmt.test, env))) {
          return await this._execBlock(stmt.body, env);
        }
        for (const el of stmt.elifs) {
          if (el.line) this.onLine(el.line);
          if (pyTruthy(await this._evalExpr(el.test, env))) {
            return await this._execBlock(el.body, env);
          }
        }
        if (stmt.orelse.length) return await this._execBlock(stmt.orelse, env);
        return null;
      }
      case 'While': {
        while (pyTruthy(await this._evalExpr(stmt.test, env))) {
          await this._checkTick();
          const sig = await this._execBlock(stmt.body, env);
          if (sig instanceof BreakSignal) break;
          if (sig instanceof ContinueSignal) continue;
          if (sig instanceof ReturnSignal) return sig;
        }
        return null;
      }
      case 'For': {
        const iterable = toIterable(await this._evalExpr(stmt.iter, env), stmt.line);
        for (const item of iterable) {
          await this._checkTick();
          await this._assignTarget(stmt.target, item, env);
          const sig = await this._execBlock(stmt.body, env);
          if (sig instanceof BreakSignal) break;
          if (sig instanceof ContinueSignal) continue;
          if (sig instanceof ReturnSignal) return sig;
        }
        return null;
      }
      case 'FuncDef': {
        const defaults = [];
        for (const p of stmt.params) {
          defaults.push(p.defaultVal ? await this._evalExpr(p.defaultVal, env) : undefined);
        }
        const fnObj = {
          __pyFunc: true,
          name: stmt.name,
          isAsync: stmt.isAsync,
          params: stmt.params.map((p) => p.name),
          defaults,
          body: stmt.body,
          closure: env,
          line: stmt.line,
        };
        env.set(stmt.name, fnObj);
        return null;
      }
      default:
        throw new PyError('RuntimeError', `unknown statement ${stmt.kind}`, stmt.line);
    }
  }

  async _assignTarget(target, val, env) {
    if (target.kind === 'Name') {
      env.set(target.id, val);
      return;
    }
    if (target.kind === 'Tuple' || target.kind === 'List') {
      const items = toIterable(val, target.line);
      if (items.length !== target.items.length) {
        throw new PyError('ValueError', `expected ${target.items.length} values to unpack, got ${items.length}`, target.line);
      }
      for (let k = 0; k < target.items.length; k++) {
        await this._assignTarget(target.items[k], items[k], env);
      }
      return;
    }
    if (target.kind === 'Subscript') {
      const obj = await this._evalExpr(target.obj, env);
      const idx = await this._evalExpr(target.index, env);
      if (Array.isArray(obj)) {
        const i = idx < 0 ? obj.length + idx : idx;
        obj[i] = val;
      } else if (obj && typeof obj === 'object') {
        obj[String(idx)] = val;
      }
      return;
    }
    if (target.kind === 'Attr') {
      const obj = await this._evalExpr(target.obj, env);
      obj[target.attr] = val;
      return;
    }
    throw new PyError('SyntaxError', 'cannot assign to expression', target.line);
  }

  async _evalExpr(node, env) {
    switch (node.kind) {
      case 'Literal': return node.value;
      case 'FString': return await this._evalFString(node.raw, env, node.line);
      case 'Name': return env.get(node.id, node.line);
      case 'Tuple': {
        const items = [];
        for (const it of node.items) items.push(await this._evalExpr(it, env));
        return pyTuple(items);
      }
      case 'List': {
        const items = [];
        for (const it of node.items) items.push(await this._evalExpr(it, env));
        return items;
      }
      case 'ListComp': {
        const out = [];
        const iter = toIterable(await this._evalExpr(node.iter, env), node.line);
        const child = new Env(env, env.globals);
        for (const item of iter) {
          await this._assignTarget(node.target, item, child);
          if (!node.cond || pyTruthy(await this._evalExpr(node.cond, child))) {
            out.push(await this._evalExpr(node.elt, child));
          }
        }
        return out;
      }
      case 'Dict': {
        const obj = {};
        for (const { key, val } of node.entries) {
          const k = await this._evalExpr(key, env);
          obj[String(k)] = await this._evalExpr(val, env);
        }
        return obj;
      }
      case 'UnaryOp': {
        const v = await this._evalExpr(node.operand, env);
        if (node.op === 'not') return !pyTruthy(v);
        if (node.op === '-') return -pyNum(v, node.line);
        if (node.op === '+') return +pyNum(v, node.line);
        if (node.op === '~') return ~Math.trunc(pyNum(v, node.line));
        throw new PyError('SyntaxError', `unknown unary op ${node.op}`, node.line);
      }
      case 'BinOp': {
        const l = await this._evalExpr(node.left, env);
        const r = await this._evalExpr(node.right, env);
        return pyBinOp(node.op, l, r, node.line);
      }
      case 'BoolOp': {
        const l = await this._evalExpr(node.left, env);
        if (node.op === 'and') return pyTruthy(l) ? await this._evalExpr(node.right, env) : l;
        return pyTruthy(l) ? l : await this._evalExpr(node.right, env);
      }
      case 'Compare': {
        let left = await this._evalExpr(node.left, env);
        for (let k = 0; k < node.ops.length; k++) {
          const right = await this._evalExpr(node.comparators[k], env);
          if (!pyCompareOp(node.ops[k], left, right)) return false;
          left = right;
        }
        return true;
      }
      case 'Ternary':
        return pyTruthy(await this._evalExpr(node.test, env))
          ? await this._evalExpr(node.body, env)
          : await this._evalExpr(node.orelse, env);
      case 'Lambda': {
        const defaults = [];
        for (const p of node.params) {
          defaults.push(p.defaultVal ? await this._evalExpr(p.defaultVal, env) : undefined);
        }
        return {
          __pyFunc: true,
          name: '<lambda>',
          isAsync: false,
          params: node.params.map((p) => p.name),
          defaults,
          body: [{ kind: 'Return', value: node.body, line: node.line }],
          closure: env,
          line: node.line,
        };
      }
      case 'Attr': {
        const obj = await this._evalExpr(node.obj, env);
        return this._getAttr(obj, node.attr, node.line);
      }
      case 'Subscript': {
        const obj = await this._evalExpr(node.obj, env);
        const idx = await this._evalExpr(node.index, env);
        if (Array.isArray(obj) || typeof obj === 'string') {
          const i = idx < 0 ? obj.length + idx : idx;
          if (i < 0 || i >= obj.length) throw new PyError('IndexError', 'index out of range', node.line);
          return obj[i];
        }
        if (obj && typeof obj === 'object') {
          const key = String(idx);
          if (!(key in obj)) throw new PyError('KeyError', key, node.line);
          return obj[key];
        }
        throw new PyError('TypeError', 'object is not subscriptable', node.line);
      }
      case 'Slice': {
        const obj = await this._evalExpr(node.obj, env);
        const len = obj.length;
        const step = node.step ? Math.trunc(await this._evalExpr(node.step, env)) : 1;
        if (step === 0) throw new PyError('ValueError', 'slice step cannot be zero', node.line);
        let lo = node.lower ? Math.trunc(await this._evalExpr(node.lower, env)) : (step > 0 ? 0 : len - 1);
        let hi = node.upper ? Math.trunc(await this._evalExpr(node.upper, env)) : (step > 0 ? len : -len - 1);
        if (lo < 0) lo = Math.max(step > 0 ? 0 : -1, len + lo);
        if (hi < 0) hi = Math.max(step > 0 ? 0 : -1, len + hi);
        if (lo > len) lo = step > 0 ? len : len - 1;
        if (hi > len) hi = len;
        const out = [];
        if (step > 0) for (let k = lo; k < hi; k += step) out.push(obj[k]);
        else for (let k = lo; k > hi; k += step) out.push(obj[k]);
        return typeof obj === 'string' ? out.join('') : (obj[PY_TUPLE] ? pyTuple(out) : out);
      }
      case 'Call': {
        const fn = await this._evalExpr(node.func, env);
        const args = [];
        for (const a of node.args) args.push(await this._evalExpr(a, env));
        const kwargs = {};
        for (const kw of node.kwargs) kwargs[kw.key] = await this._evalExpr(kw.value, env);
        return await this.callCallable(fn, args, kwargs, node.line);
      }
      case 'Await': {
        const val = await this._evalExpr(node.value, env);
        if (val && val.__pyCoro && typeof val.start === 'function') {
          const res = await val.start();
          if (this.isCancelled()) throw new SimCancelledError();
          return res;
        }
        if (val && typeof val.then === 'function') {
          const res = await val;
          if (this.isCancelled()) throw new SimCancelledError();
          return res;
        }
        return val;
      }
      default:
        throw new PyError('RuntimeError', `unknown expression ${node.kind}`, node.line);
    }
  }

  async _evalFString(raw, env, line) {
    let out = '';
    let i = 0;
    while (i < raw.length) {
      if (raw[i] === '{') {
        if (raw[i + 1] === '{') { out += '{'; i += 2; continue; }
        let depth = 1;
        let j = i + 1;
        while (j < raw.length && depth > 0) {
          if (raw[j] === '{') depth++;
          else if (raw[j] === '}') depth--;
          j++;
        }
        const inner = raw.slice(i + 1, j - 1);
        const colon = inner.indexOf(':');
        const exprStr = (colon >= 0 ? inner.slice(0, colon) : inner).trim();
        const fmt = colon >= 0 ? inner.slice(colon + 1) : '';
        const exprAst = parse(exprStr).body[0]?.expr;
        const val = await this._evalExpr(exprAst, env);
        if (fmt) {
          const m = fmt.match(/\.(\d+)f$/);
          if (m && typeof val === 'number') out += val.toFixed(Number(m[1]));
          else out += pyStr(val);
        } else {
          out += pyStr(val);
        }
        i = j;
      } else if (raw[i] === '}' && raw[i + 1] === '}') {
        out += '}';
        i += 2;
      } else {
        out += raw[i++];
      }
    }
    return out;
  }

  _getAttr(obj, attr, line) {
    if (obj === null || obj === undefined) {
      throw new PyError('AttributeError', `'NoneType' object has no attribute '${attr}'`, line);
    }
    if (typeof obj === 'string') {
      const strMethods = {
        upper: nativeFn(() => obj.toUpperCase()),
        lower: nativeFn(() => obj.toLowerCase()),
        strip: nativeFn(() => obj.trim()),
        split: nativeFn(([sep]) => (sep === undefined ? obj.trim().split(/\s+/).filter(Boolean) : obj.split(sep))),
        join: nativeFn(([seq]) => toIterable(seq, line).map(pyStr).join(obj)),
        replace: nativeFn(([a, b]) => obj.split(a).join(b)),
        startswith: nativeFn(([p]) => obj.startsWith(p)),
        endswith: nativeFn(([p]) => obj.endsWith(p)),
      };
      if (attr in strMethods) return strMethods[attr];
    }
    if (Array.isArray(obj)) {
      const listMethods = {
        append: nativeFn(([x]) => { obj.push(x); return null; }),
        pop: nativeFn(([i]) => (i === undefined ? obj.pop() : obj.splice(i < 0 ? obj.length + i : i, 1)[0])),
        clear: nativeFn(() => { obj.length = 0; return null; }),
        extend: nativeFn(([seq]) => { obj.push(...toIterable(seq, line)); return null; }),
        insert: nativeFn(([i, x]) => { obj.splice(i, 0, x); return null; }),
        copy: nativeFn(() => obj.slice()),
        reverse: nativeFn(() => { obj.reverse(); return null; }),
        sort: nativeFn(([], kw) => {
          obj.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
          if (kw.reverse) obj.reverse();
          return null;
        }),
        index: nativeFn(([x]) => {
          const idx = obj.findIndex((v) => pyEq(v, x));
          if (idx < 0) throw new PyError('ValueError', `${x} is not in list`, line);
          return idx;
        }),
        count: nativeFn(([x]) => obj.filter((v) => pyEq(v, x)).length),
      };
      if (attr in listMethods) return listMethods[attr];
    }
    if (typeof obj === 'object' && obj.constructor === Object && !(attr in obj)) {
      const dictMethods = {
        get: nativeFn(([k, def = null]) => (String(k) in obj ? obj[String(k)] : def)),
        keys: nativeFn(() => Object.keys(obj)),
        values: nativeFn(() => Object.values(obj)),
        items: nativeFn(() => Object.entries(obj).map(([k, v]) => pyTuple([k, v]))),
        pop: nativeFn(([k, def]) => {
          const ks = String(k);
          if (ks in obj) { const v = obj[ks]; delete obj[ks]; return v; }
          if (def !== undefined) return def;
          throw new PyError('KeyError', ks, line);
        }),
      };
      if (attr in dictMethods) return dictMethods[attr];
    }
    if (typeof obj === 'object' && attr in obj) return obj[attr];
    throw new PyError('AttributeError', `object has no attribute '${attr}'`, line);
  }

  async callCallable(fn, args = [], kwargs = {}, line = null) {
    if (!fn) throw new PyError('TypeError', `'${pyStr(fn)}' object is not callable`, line);
    if (typeof fn === 'function' && fn[NATIVE_FN]) {
      return fn(args, kwargs, this);
    }
    if (typeof fn === 'function') {
      return fn(...args);
    }
    if (fn.__pyFunc) {
      const runBody = async () => {
        const localEnv = new Env(fn.closure, fn.closure.globals);
        for (let k = 0; k < fn.params.length; k++) {
          const pname = fn.params[k];
          if (k < args.length) localEnv.vars[pname] = args[k];
          else if (pname in kwargs) localEnv.vars[pname] = kwargs[pname];
          else if (fn.defaults[k] !== undefined) localEnv.vars[pname] = fn.defaults[k];
          else throw new PyError('TypeError', `${fn.name}() missing required argument '${pname}'`, line);
        }
        const sig = await this._execBlock(fn.body, localEnv);
        return sig instanceof ReturnSignal ? sig.value : null;
      };
      if (fn.isAsync) {
        // Non-thenable coroutine handle so `runloop.run(main_1(), main_2())` passes both
        // coroutines concurrently without JS auto-awaiting main_1() during argument evaluation.
        let started = null;
        return {
          __pyCoro: true,
          start: () => (started || (started = runBody())),
        };
      }
      return await runBody();
    }
    throw new PyError('TypeError', 'object is not callable', line);
  }
}
