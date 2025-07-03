from django.test import TestCase, Client
from django.utils import timezone
from datetime import datetime
from todo.models import Task


class SampleTestCase(TestCase):
    # ① 簡単なサンプルテスト
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    # ② モデル作成（dueあり）
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()
        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    # ③ モデル作成（dueなし）
    def test_create_task2(self):
        task = Task(title='task2')
        task.save()
        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertIsNone(task.due_at)

    # ④ 締切が未来 → is_overdue は False
    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()
        self.assertFalse(task.is_overdue(current))

    # ⑤ 締切が過去 → is_overdue は True
    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()
        self.assertTrue(task.is_overdue(current))

    # ⑥ 締切がない → is_overdue は False
    def test_is_overdue_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1')  # due_at なし
        task.save()
        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    # ⑦ GETでタスクが0件でも表示できる
    def test_index_get_no_tasks(self):
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    # ⑧ POSTでタスクを1件登録できる
    def test_index_post(self):
        client = Client()
        data = {'title': 'Test Task', 'due_at': '2024-06-30 23:59:59'}
        response = client.post('/', data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)

    # ⑨ order=post → 投稿日時の新しい順で並ぶ
    def test_index_get_order_post(self):
        task1 = Task.objects.create(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task2 = Task.objects.create(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        client = Client()
        response = client.get('/?order=post')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    # ⑩ order=due → 締切の早い順で並ぶ
    def test_index_get_order_due(self):
        task1 = Task.objects.create(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task2 = Task.objects.create(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        client = Client()
        response = client.get('/?order=due')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)
