import { Pool } from 'pg';
import { IGetUsersResult, getUsers } from '../sql/users/selectAll';

export const fetchUsers = async (db: Pool): Promise<IGetUsersResult[]> => {
  return getUsers.run(undefined, db);
};
