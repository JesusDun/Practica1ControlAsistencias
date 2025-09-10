const mysql = require('mysql2/promise');
require('dotenv').config();

// Configuración de conexión a MySQL
const dbConfig = {
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  acquireTimeout: 60000,
  timeout: 60000,
  reconnect: true
};

// Pool de conexiones
const pool = mysql.createPool(dbConfig);

// Función para probar la conexión
const testConnection = async () => {
  try {
    const connection = await pool.getConnection();
    console.log('Conectado exitosamente a MySQL');
    connection.release();
    return true;
  } catch (error) {
    console.error('Error conectando a MySQL:', error.message);
    return false;
  }
};

// Función helper para ejecutar queries
const executeQuery = async (query, params = []) => {
  try {
    const [rows] = await pool.execute(query, params);
    return rows;
  } catch (error) {
    console.error('Error ejecutando query:', error);
    throw error;
  }
};

module.exports = {
  pool,
  testConnection,
  executeQuery
};
