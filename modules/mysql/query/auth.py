# default
insertUser = "INSERT INTO users (email, phonenum, username, password, created_at, last_used) VALUES ('{}', '{}', '{}', '{}', '{}', '{}');"
selectUser = "SELECT * FROM users WHERE {} = '{}';"
updateUser = "UPDATE users SET {} = '{}' WHERE {} = '{}';"
deleteUser = "DELETE FROM users WHERE {} = '{}';"