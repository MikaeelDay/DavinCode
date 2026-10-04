from django.urls import path

from . import views

urlpatterns = [
    path('', views.question_list, name='question_list'),
    path('question/<int:id>/', views.question_detail, name='question_detail'),
    path('question/<int:id>/answer/', views.add_answer, name='add_answer'),
    path('question/<int:id>/edit/', views.edit_question, name='edit_question'),
    path('answer/<int:answer_id>/edit/', views.edit_answer, name='edit_answer'),
    path('answer/<int:answer_id>/reply/', views.add_comment, name='add_comment'),
    path('add/', views.add_question, name='add_question'),
    path('signup/', views.sign_up, name='signup'),
    path('search/', views.search, name='search'),
    path('profile/', views.profile_view, name='my_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('answer/<int:answer_id>/vote/<str:vote_type>/', views.vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/accept/', views.accept_answer, name='accept_answer'),
]
