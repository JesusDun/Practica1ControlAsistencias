const jwt = require('jsonwebtoken');
const { executeQuery } = require('../config/database');

// Middleware para verificar JWT
const verifyToken = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader) {
      return res.status(401).json({ 
        error: 'Token de acceso requerido',
        message: 'Debe incluir Authorization header' 
      });
    }

    const token = authHeader.split(' ')[1]; // Bearer TOKEN
    
    if (!token) {
      return res.status(401).json({ 
        error: 'Formato de token inválido',
        message: 'Use formato: Bearer <token>' 
      });
    }

    // Verificar token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Opcional: Verificar si el usuario aún existe
    const user = await executeQuery(
      'SELECT idEmpleado, nombreEmpleado, numero FROM empleados WHERE idEmpleado = ?',
      [decoded.userId]
    );

    if (user.length === 0) {
      return res.status(401).json({ 
        error: 'Usuario no encontrado',
        message: 'El token corresponde a un usuario que ya no existe' 
      });
    }

    // Agregar info del usuario al request
    req.user = {
      id: decoded.userId,
      name: user[0].nombreEmpleado,
      numero: user[0].numero
    };

    next();
  } catch (error) {
    console.error('Error verificando token:', error);
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ 
        error: 'Token expirado',
        message: 'Debe autenticarse nuevamente' 
      });
    }
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({ 
        error: 'Token inválido',
        message: 'El token proporcionado no es válido' 
      });
    }

    res.status(500).json({ 
      error: 'Error de autenticación',
      message: 'Error interno verificando credenciales' 
    });
  }
};

// Middleware opcional (para rutas que pueden funcionar con o sin auth)
const optionalAuth = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.split(' ')[1];
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      const user = await executeQuery(
        'SELECT idEmpleado, nombreEmpleado, numero FROM empleados WHERE idEmpleado = ?',
        [decoded.userId]
      );

      if (user.length > 0) {
        req.user = {
          id: decoded.userId,
          name: user[0].nombreEmpleado,
          numero: user[0].numero
        };
      }
    }
    
    next();
  } catch (error) {
    // En auth opcional, continuamos sin usuario autenticado
    next();
  }
};

module.exports = {
  verifyToken,
  optionalAuth
};
