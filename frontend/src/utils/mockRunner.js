// Enhanced mock runner with better simulation
export async function runCodeMock(code, tests, language = 'javascript'){
  // fake execution delay (randomize slightly to feel more realistic)
  const delay = 600 + Math.random() * 400;
  await new Promise(r => setTimeout(r, delay));

  // More sophisticated mock behavior:
  // 1. If no code, all tests fail with "no solution provided"
  if (!code || code.trim() === '') {
    return { 
      success: false, 
      results: tests.map(t => ({ 
        input: t.input, 
        expected: t.expected, 
        output: 'Error: No solution provided',
        passed: false,
        error: 'No code submitted'
      }))
    };
  }

  // 2. If code doesn't contain return or solution pattern, fail with appropriate message
  if (!code.includes('return') && !code.includes('solution')) {
    return { 
      success: false,
      results: tests.map((t, i) => ({ 
        input: t.input, 
        expected: t.expected, 
        output: i === 0 ? 'undefined' : '[]',
        passed: false,
        error: 'Function does not return a value'
      }))
    };
  }
  
  // 3. If code has syntax errors (very basic check), fail with syntax error
  const syntaxErrors = mockSyntaxCheck(code, language);
  if (syntaxErrors.length > 0) {
    return {
      success: false,
      results: tests.map(t => ({ 
        input: t.input, 
        expected: t.expected, 
        output: 'Error: ' + syntaxErrors[0].message,
        passed: false,
        error: 'Syntax error'
      })),
      errors: syntaxErrors
    };
  }
  
  // 4. For more realistic behavior, make some tests pass and some fail based on code quality
  const containsForLoop = code.includes('for (') || code.includes('for(');
  const containsMap = code.includes('.map(');
  const containsFilter = code.includes('.filter(');
  const seemsOptimized = containsMap || containsFilter;
  
  // Pass rate based on code quality signals
  const passRate = seemsOptimized ? 1.0 : (containsForLoop ? 0.7 : 0.4);
  
  // Generate mock results with varying pass rates
  return {
    success: passRate === 1.0, // Only fully successful if all tests pass
    results: tests.map((t, i) => {
      const shouldPass = Math.random() < passRate;
      return {
        input: t.input,
        expected: t.expected,
        output: shouldPass ? t.expected : (i % 2 === 0 ? '[]' : 'undefined'),
        passed: shouldPass,
        time: Math.round(Math.random() * 20) + 'ms',
        error: shouldPass ? null : 'Output does not match expected result'
      };
    })
  };
}

// Basic mock syntax checker
function mockSyntaxCheck(code, language) {
  const errors = [];
  
  // Very simplistic checks
  if (code.includes('{') && !code.includes('}')) {
    errors.push({
      message: 'Missing closing brace',
      line: code.split('\n').findIndex(line => line.includes('{')) + 1
    });
  }
  
  if (code.includes('(') && !code.includes(')')) {
    errors.push({
      message: 'Missing closing parenthesis',
      line: code.split('\n').findIndex(line => line.includes('(')) + 1
    });
  }
  
  // JavaScript/TypeScript specific checks
  if (language === 'javascript' || language === 'typescript') {
    const lines = code.split('\n');
    lines.forEach((line, i) => {
      // Check for missing semicolons at statement ends (simplified)
      if (line.trim().length > 0 && 
          !line.trim().endsWith(';') && 
          !line.trim().endsWith('{') && 
          !line.trim().endsWith('}') &&
          !line.trim().endsWith('(') &&
          !line.trim().startsWith('//') &&
          !line.trim().startsWith('/*') &&
          !line.trim().endsWith('*/') &&
          !line.trim().startsWith('import') &&
          !line.trim().startsWith('export')) {
        // This is a very naive check and would flag many valid lines
        // We'll be very lenient for the mock
        if (Math.random() < 0.2) { // Only flag some to avoid being too aggressive
          errors.push({
            message: 'Missing semicolon',
            line: i + 1
          });
        }
      }
    });
  }
  
  return errors;
}
