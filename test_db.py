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


service.add_relation(from_user='link1', to_user='link2', status='Favorite')
service.add_relation('link1', 'link3', 'Favorite')
service.add_relation('link1', 'link4', 'Blacklist')

favorites = service.get_favorite_list('link1')
print(favorites)

blocked = service.get_blocked_list('link1')
print(blocked)

