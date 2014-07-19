from django.test import TestCase

from agora.models import Forum, ForumCategory


class ForumCategoryTests(TestCase):

    def test_unicode_method(self):
        cat = ForumCategory(title="Software")
        self.assertEquals(str(cat), cat.title)

    def test_get_absolute_url(self):
        cat = ForumCategory.objects.create(title="Software")
        self.assertEquals(cat.get_absolute_url(), "/category/1/")

    def test_forums_ordered_properly(self):
        cat = ForumCategory.objects.create(title="Software")
        Forum.objects.create(category=cat, title="Python", description="Python software")
        Forum.objects.create(category=cat, title="Swift", description="Swift software")
        Forum.objects.create(category=cat, title="Basic", description="Old software")
        forums = cat.forums
        self.assertEquals(forums[0].title, "Basic")
        self.assertEquals(forums[1].title, "Python")
        self.assertEquals(forums[2].title, "Swift")


class ForumTests(TestCase):

    def test_forum_thread_count_is_zero(self):
        f = Forum.objects.create(title="Python", description="Python software")
        self.assertEquals(f.thread_count, 0)

    def test_inc_views(self):
        f = Forum.objects.create(title="Python", description="Python software")
        self.assertEquals(f.view_count, 0)
        f.inc_views()
        self.assertEquals(f.view_count, 1)
