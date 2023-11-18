/* schema.sql */

CREATE TABLE IF NOT EXISTS post (
        id INTEGER NOT NULL, 
        title VARCHAR(255), 
        text TEXT, 
        publish_date DATETIME DEFAULT (CURRENT_TIMESTAMP), 
        user_id INTEGER, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES user (id)
);