from django.urls import path
from . import views

app_name = 'drawings'

urlpatterns = [
    # Dashboard
    path('',                                    views.DrawingsDashboardView.as_view(),    name='dashboard'),
    # Drawing register
    path('register/',                           views.DrawingListView.as_view(),           name='drawing_list'),
    path('register/create/',                    views.DrawingCreateView.as_view(),         name='drawing_create'),
    path('register/<int:pk>/',                  views.DrawingDetailView.as_view(),         name='drawing_detail'),
    path('register/<int:pk>/edit/',             views.DrawingUpdateView.as_view(),         name='drawing_update'),
    path('register/<int:pk>/revise/',           views.DrawingRevisionCreateView.as_view(), name='drawing_revise'),
    # RFI
    path('rfi/',                                views.RFIListView.as_view(),               name='rfi_list'),
    path('rfi/create/',                         views.RFICreateView.as_view(),             name='rfi_create'),
    path('rfi/<int:pk>/',                       views.RFIDetailView.as_view(),             name='rfi_detail'),
    path('rfi/<int:pk>/edit/',                  views.RFIUpdateView.as_view(),             name='rfi_update'),
    path('rfi/<int:pk>/submit/',                views.RFISubmitView.as_view(),             name='rfi_submit'),
    path('rfi/<int:pk>/review/',                views.RFIReviewView.as_view(),             name='rfi_review'),
    path('rfi/<int:pk>/answer/',                views.RFIAnswerView.as_view(),             name='rfi_answer'),
    path('rfi/<int:pk>/close/',                 views.RFICloseView.as_view(),              name='rfi_close'),
    path('rfi/<int:pk>/void/',                  views.RFIVoidView.as_view(),               name='rfi_void'),
]
