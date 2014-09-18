from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
"""
athletes, c = Group.objects.get_or_create(name='athletes')
coaches, c = Group.objects.get_or_create(name='coaches')

ct = ContentType.objects.get(app_label='auth', model='user', name='user')

can_create_workout, c = Permission.objects.get_or_create(name='Can create workout',
        codename='can_create_workout', content_type=ct)
can_add_tag, c = Permission.objects.get_or_create(name='Can add tag', codename='can_add_tag',
        content_type=ct)

athletes.permissions.add(can_add_tag.id)
coaches.permissions.add(can_create_workout.id)
"""
