instructions = [
    'SET FOREIGN_KEY_CHECKS=0;',
    'DROP TABLE IF EXISTS user;',
    'SET FOREIGN_KEY_CHECKS=1;',
    """
        -- Creación de la tabla codigos_acceso
        CREATE TABLE codigos_acceso (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            disponible BOOLEAN
        );

        -- Creación de la tabla hogares
        CREATE TABLE hogares (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            direccion VARCHAR(255) NOT NULL,
            paquete ENUM('basico', 'premium', 'deluxe') NOT NULL
        );

        -- Creación de la tabla users
        CREATE TABLE users (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            apellido VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password VARCHAR(15) NOT NULL,
            telefono VARCHAR(13) NOT NULL,
            rol ENUM('admin', 'user', 'guest') NOT NULL,
            chat_id VARCHAR(255),
            hogar_id INT(10),
            codigo_acceso_id INT(10),
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (codigo_acceso_id) REFERENCES codigos_acceso(id)
        );
    """
]