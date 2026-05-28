from django.urls import path
from . import views

app_name = 'subcontractors'

urlpatterns = [
    # Dashboard
    path('',                                                views.SubcontractorDashboardView.as_view(),  name='dashboard'),
    # Subcontractor master
    path('list/',                                           views.SubcontractorListView.as_view(),        name='contractor_list'),
    path('create/',                                         views.SubcontractorCreateView.as_view(),      name='contractor_create'),
    path('<int:pk>/',                                       views.SubcontractorDetailView.as_view(),      name='contractor_detail'),
    path('<int:pk>/edit/',                                  views.SubcontractorUpdateView.as_view(),      name='contractor_update'),
    # Contracts
    path('contracts/',                                      views.ContractListView.as_view(),             name='contract_list'),
    path('contracts/create/',                               views.ContractCreateView.as_view(),           name='contract_create'),
    path('contracts/<int:pk>/',                             views.ContractDetailView.as_view(),           name='contract_detail'),
    path('contracts/<int:pk>/edit/',                        views.ContractUpdateView.as_view(),           name='contract_update'),
    path('contracts/<int:pk>/status/',                      views.ContractStatusView.as_view(),           name='contract_status'),
    # Payment Claims
    path('contracts/<int:contract_pk>/claims/create/',      views.PaymentClaimCreateView.as_view(),       name='claim_create'),
    path('claims/<int:pk>/',                                views.PaymentClaimDetailView.as_view(),       name='claim_detail'),
    path('claims/<int:pk>/submit/',                         views.PaymentClaimSubmitView.as_view(),       name='claim_submit'),
    path('claims/<int:pk>/certify/',                        views.PaymentClaimCertifyView.as_view(),      name='claim_certify'),
    path('claims/<int:pk>/pay/',                            views.PaymentClaimPayView.as_view(),          name='claim_pay'),
    path('claims/<int:pk>/reject/',                         views.PaymentClaimRejectView.as_view(),       name='claim_reject'),
]
