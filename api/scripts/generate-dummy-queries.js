#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const sqlDir = path.join(__dirname, '../src/sql/tickets');
const files = fs.readdirSync(sqlDir).filter(f => f.endsWith('.sql'));

files.forEach(file => {
  const baseName = path.basename(file, '.sql');
  const queryFile = path.join(sqlDir, `${baseName}.queries.ts`);
  
  // Generate minimal type-safe dummy content
  const content = `
// Auto-generated dummy file for CI
export interface IParams {}
export interface IResult {}

export const ${baseName} = {
  run: async (params: any, client?: any): Promise<IResult[]> => {
    return [];
  }
};

// Export any additional types that might be referenced
export type I${baseName.charAt(0).toUpperCase() + baseName.slice(1)}Params = IParams;
export type I${baseName.charAt(0).toUpperCase() + baseName.slice(1)}Result = IResult;
`;

  fs.writeFileSync(queryFile, content);
  console.log(`Generated dummy query file: ${queryFile}`);
});