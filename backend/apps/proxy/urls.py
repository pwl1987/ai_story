from django.urls import path

from . import views

app_name = "proxy"

urlpatterns = [
    # Story 9.8: 代理选择列表 API
    path("select/", views.ProxySelectViewSet.as_view({"get": "list"}), name="proxy-select"),
    # Story 9.9: 测试代理连接 API
    path("<int:pk>/test_connection/", views.TestConnectionView.as_view(), name="test-connection"),
]
