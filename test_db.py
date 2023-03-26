from VKinder_db.db import connect_to_db


service = connect_to_db('vkinder_db')

# tests
user = ['Ivan', 'Ivanov', 'Male', 'Moskow', 'link1']
service.add_user(user)
user = ['Anna', 'Ivanova', 'Female', 'Moskow', 'link2']
service.add_user(user)
user = ['Anna', 'Svetlanova', 'Female', 'Moskow', 'link3']
service.add_user(user)
user = ['Sergey', 'Maslukov', 'Male', 'Moskow', 'link4']
service.add_user(user)

connection = ['link1', 'link2']
service.add_relation(connection, 1)
connection = ['link1', 'link3']
service.add_relation(connection, 1)
connection = ['link1', 'link4']
service.add_relation(connection, 2)

favorites = service.get_favorite_list('link1')
print(favorites)

blocked = service.get_blocked_list('link1')
print(blocked)

