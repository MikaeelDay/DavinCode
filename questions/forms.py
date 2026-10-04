import nh3
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Answer, Comment, Question

# فقط تگ‌هایی که ادیتور تولید می‌کند مجازند؛ بقیه (مثل script) حذف می‌شوند
ALLOWED_TAGS = {'p', 'br', 'strong', 'b', 'em', 'i', 'a', 'ul', 'ol', 'li', 'blockquote',
                'pre', 'code', 'h2', 'h3', 'h4', 'figure', 'img'}


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='ایمیل')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email


class QuestionForm(forms.ModelForm):
    # CKEditor فیلد اصلی را مخفی می‌کند؛ با required مرورگر بی‌صدا جلوی ارسال را می‌گیرد
    # اعتبارسنجی در سرور همچنان انجام می‌شود
    use_required_attribute = False
    body = forms.CharField(widget=CKEditor5Widget(config_name='default'), label='متن سوال')

    class Meta:
        model = Question
        fields = ['title', 'body']
        labels = {'title': 'عنوان سوال'}
        widgets = {'title': forms.TextInput(attrs={'placeholder': 'مشکل‌ات را در یک جمله بنویس'})}

    def clean_body(self):
        return nh3.clean(self.cleaned_data['body'], tags=ALLOWED_TAGS,
                         attributes={'a': {'href'}, 'img': {'src', 'alt'}})


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['body']
        labels = {'body': 'پاسخ شما'}
        widgets = {'body': forms.Textarea(attrs={'rows': 6, 'placeholder': 'پاسخ خود را بنویسید...'})}

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if len(body) < 5:
            raise forms.ValidationError('پاسخ خیلی کوتاه است.')
        return body


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {'body': forms.Textarea(attrs={'rows': 2, 'maxlength': 500, 'placeholder': 'ریپلای شما...'})}

    def clean_body(self):
        body = self.cleaned_data['body'].strip()
        if len(body) < 2:
            raise forms.ValidationError('ریپلای خیلی کوتاه است.')
        return body
