#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const sqlDir = path.join(__dirname, '../src/sql/tickets');
const files = fs.readdirSync(sqlDir).filter(f => f.endsWith('.sql'));

files.forEach(file => {
  const baseName = path.basename(file, '.sql');
  const queryFile = path.join(sqlDir, `${baseName}.queries.ts`);
  
  // Generate more complete dummy types
  const camelName = baseName.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
  const pascalName = camelName.charAt(0).toUpperCase() + camelName.slice(1);
  
  // Generate minimal type-safe dummy content with common properties
  const content = `
// Auto-generated dummy file for CI
export interface I${pascalName}Params {
  [key: string]: any;
}

export interface I${pascalName}Result {
  id?: number;
  name?: string;
  email?: string;
  role?: string;
  ticket_id?: string;
  requestor_id?: number;
  requestor_name?: string;
  account_id?: number;
  account_name?: string;
  category_id?: number;
  category_name?: string;
  category_detail_id?: number;
  category_detail_name?: string;
  request_channel_id?: number;
  request_channel_name?: string;
  summary?: string;
  description?: string;
  person_in_charge_id?: number;
  person_in_charge_name?: string;
  status_id?: number;
  status_name?: string;
  reception_date_time?: string;
  scheduled_completion_date?: string;
  completion_date?: string;
  actual_effort_hours?: number;
  response_category_id?: number;
  response_category_name?: string;
  response_details?: string;
  has_defect?: boolean;
  external_ticket_id?: string;
  remarks?: string;
  timestamp?: string;
  user_id?: number;
  user_name?: string;
  comment?: string;
  field_name?: string;
  old_value?: string;
  new_value?: string;
  seq_value?: number;
  updated_by_name?: string;
  order_no?: number;
  parent_category?: string;
  file_name?: string;
  file_url?: string;
  uploaded_at?: string;
  [key: string]: any;
}

export const ${camelName} = {
  run: async (params?: I${pascalName}Params, client?: any): Promise<I${pascalName}Result[]> => {
    return [];
  }
};

// Re-export commonly used types
export type IResult = I${pascalName}Result;
export type IParams = I${pascalName}Params;
`;

  fs.writeFileSync(queryFile, content);
  console.log(`Generated dummy query file: ${queryFile}`);
});