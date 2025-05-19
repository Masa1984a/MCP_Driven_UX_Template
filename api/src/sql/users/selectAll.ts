import { Pool } from 'pg';

export interface IGetUsersParams {}

export interface IGetUsersResult {
  id: string;
  name: string;
  email: string;
  role: string;
}

export const getUsers = {
  run: async (_params: IGetUsersParams | undefined, db: Pool): Promise<IGetUsersResult[]> => {
    const query = `SELECT id, name, email, role FROM mcp_ux.users ORDER BY name ASC;`;
    const result = await db.query<IGetUsersResult>(query);
    return result.rows;
  }
};
