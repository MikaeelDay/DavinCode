from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from django.utils import timezone

from .forms import AnswerForm, CommentForm, QuestionForm, SignupForm
from .models import Answer, Profile, Question

PAGE_SIZE = 10


def _paginate(request, qs):
    return Paginator(qs, PAGE_SIZE).get_page(request.GET.get('page'))


def _questions():
    return (Question.objects.select_related('author')
            .annotate(answer_count=Count('answer', distinct=True))
            .order_by('-created_at'))


def question_list(request):
    page = _paginate(request, _questions())
    return render(request, 'questions/list.html', {'page': page})


def question_detail(request, id):
    question = get_object_or_404(Question.objects.select_related('author'), id=id)
    answers = (question.answer_set.select_related('author').prefetch_related('comment_set__author')
               .annotate(score=Count('upvotes', distinct=True) - Count('downvotes', distinct=True))
               .order_by('-is_accepted', '-score', 'created_at'))
    return render(request, 'questions/detail.html',
                  {'question': question, 'answers': answers, 'form': AnswerForm(), 'cform': CommentForm()})


@login_required
def add_question(request):
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        question = form.save(commit=False)
        question.author = request.user
        question.save()
        return redirect('question_detail', question.id)
    return render(request, 'questions/add_questions.html', {'form': form})


@login_required
def edit_question(request, id):
    question = get_object_or_404(Question, id=id)
    if question.author_id != request.user.id:
        raise PermissionDenied
    form = QuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        q = form.save(commit=False)
        q.edited_at = timezone.now()
        q.save()
        return redirect('question_detail', q.id)
    return render(request, 'questions/add_questions.html', {'form': form, 'editing': True})


@login_required
def edit_answer(request, answer_id):
    answer = get_object_or_404(Answer.objects.select_related('question'), id=answer_id)
    if answer.author_id != request.user.id:
        raise PermissionDenied
    form = AnswerForm(request.POST or None, instance=answer)
    if request.method == 'POST' and form.is_valid():
        a = form.save(commit=False)
        a.edited_at = timezone.now()
        a.save()
        return redirect(f"{reverse('question_detail', args=[answer.question_id])}#a{a.id}")
    return render(request, 'questions/edit_answer.html', {'form': form, 'answer': answer})


@login_required
@require_POST
def add_comment(request, answer_id):
    answer = get_object_or_404(Answer, id=answer_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.author, c.answer = request.user, answer
        c.save()
    return redirect(f"{reverse('question_detail', args=[answer.question_id])}#a{answer.id}")


@login_required
@require_POST
def add_answer(request, id):
    question = get_object_or_404(Question, id=id)
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(commit=False)
        answer.author, answer.question = request.user, question
        answer.save()
    return redirect('question_detail', id=question.id)


def sign_up(request):
    if request.user.is_authenticated:
        return redirect('question_list')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.save())
        return redirect('question_list')
    return render(request, 'questions/signup.html', {'form': form})


def profile_view(request, username=None):
    if username is None:
        if not request.user.is_authenticated:
            return redirect('login')
        username = request.user.username
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    context = {
        'profile_user': user, 'profile': profile,
        'questions': _questions().filter(author=user)[:20],
        'answers': Answer.objects.filter(author=user).select_related('question')[:20],
        'question_total': Question.objects.filter(author=user).count(),
        'answer_total': Answer.objects.filter(author=user).count(),
    }
    return render(request, 'profile.html', context)


@login_required
@require_POST
def vote_answer(request, answer_id, vote_type):
    if vote_type not in ('up', 'down'):
        raise Http404
    answer = get_object_or_404(Answer, id=answer_id)
    if answer.author_id != request.user.id:  # رأی به پاسخ خودت ممکن نیست
        mine, other = ((answer.upvotes, answer.downvotes) if vote_type == 'up'
                       else (answer.downvotes, answer.upvotes))
        other.remove(request.user)
        if mine.filter(pk=request.user.pk).exists():
            mine.remove(request.user)
        else:
            mine.add(request.user)
    return redirect('question_detail', id=answer.question_id)


@login_required
@require_POST
def accept_answer(request, answer_id):
    answer = get_object_or_404(Answer.objects.select_related('question'), id=answer_id)
    question = answer.question
    if request.user != question.author:  # فقط صاحب سوال
        raise Http404
    Answer.objects.filter(question=question, is_accepted=True).update(is_accepted=False)
    answer.is_accepted = True
    answer.save(update_fields=['is_accepted'])
    question.accepted_answer = answer
    question.save(update_fields=['accepted_answer'])
    return redirect('question_detail', id=question.id)


def search(request):
    query = request.GET.get('q', '').strip()[:100]
    qs = _questions().filter(Q(title__icontains=query) | Q(body__icontains=query)) if query else Question.objects.none()
    return render(request, 'questions/search_results.html', {'page': _paginate(request, qs), 'query': query})
