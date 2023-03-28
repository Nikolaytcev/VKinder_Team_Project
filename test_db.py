from VKinder_db.db import connect_to_db


service = connect_to_db('vkinder_db')

# tests
user = [1, 'Ivan', 'Ivanov', 'Male', 'Moskow', 'link1']
service.add_user(user)
user = [2, 'Anna', 'Ivanova', 'Female', 'Moskow', 'link2']
service.add_user(user)
user = [3, 'Anna', 'Svetlanova', 'Female', 'Moskow', 'link3']
service.add_user(user)
user = [4, 'Sergey', 'Maslukov', 'Male', 'Moskow', 'link4']
service.add_user(user)


service.add_relation(from_user_id=1, to_user_id=2, status='Favorite')
service.add_relation(1, 3, 'Favorite')
service.add_relation(1, 4, 'Blacklist')

favorites = service.get_favorite_list('link1')
print(favorites)

blocked = service.get_blocked_list('link1')
print(blocked)
