from django.contrib.auth.models import User
from django.db import models
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django_ckeditor_5.fields import CKEditor5Field
import html


class Question(models.Model):
    title = models.CharField(max_length=100)
    body = CKEditor5Field('Text', config_name='default')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    # اگر پاسخ پذیرفته‌شده حذف شد، خود سوال نباید پاک شود
    accepted_answer = models.ForeignKey('Answer', on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_answer')

    def __str__(self):
        return self.title

    def excerpt(self, words=28):
        return Truncator(html.unescape(strip_tags(self.body))).words(words)


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    upvotes = models.ManyToManyField(User, related_name='upvotes', blank=True)
    downvotes = models.ManyToManyField(User, related_name='downvotes', blank=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.body[:20]}...'


class Comment(models.Model):
    """ریپلای روی یک جواب"""
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.body[:30]


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', default='profiles/default.jpg')

    def has_custom_image(self):
        return bool(self.profile_image) and not self.profile_image.name.endswith('default.jpg')

    def __str__(self):
        return self.user.username
