"""
Story 9.7: Project模型proxy_id外键测试套件

测试Project模型的proxy_config外键功能：
- Phase 1: 数据库迁移测试
- Phase 2: Project创建时设置proxy_id
- Phase 3: Project修改proxy_id
- Phase 4: 级联删除测试（SET_NULL策略）
- Phase 5: 反向关联查询测试
- Phase 6: API序列化测试

@Author: Epic 9 Team
@Created: 2026-01-31
@Story: 9.7 - Project模型proxy_id外键
"""

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.projects.models import Project
from apps.proxy.models import ProxyConfig, ProxyProtocol

User = get_user_model()


class DatabaseMigrationTest(TestCase):
    """Phase 1: 数据库迁移测试"""

    def test_proxy_config_field_exists(self):
        """AC[场景1]: proxy_config字段已添加到Project模型"""
        # 验证字段存在
        field = Project._meta.get_field("proxy_config")
        self.assertIsNotNone(field)
        self.assertEqual(field.verbose_name, "代理配置")
        self.assertEqual(field.related_model, ProxyConfig)

    def test_proxy_config_field_is_nullable(self):
        """AC[场景1]: proxy_config字段允许NULL（向后兼容）"""
        field = Project._meta.get_field("proxy_config")
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_proxy_config_on_delete_set_null(self):
        """AC[场景1]: on_delete设置为SET_NULL"""
        from django.db.models import ForeignKey

        field = Project._meta.get_field("proxy_config")
        self.assertIsInstance(field, ForeignKey)
        self.assertEqual(field.remote_field.on_delete.__name__, "SET_NULL")

    def test_proxy_config_related_name(self):
        """AC[场景7]: related_name='projects'正确配置"""
        field = Project._meta.get_field("proxy_config")
        self.assertEqual(field.remote_field.related_name, "projects")


class ProjectCreationWithProxyTest(TestCase):
    """Phase 2: Project创建时设置proxy_id"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
            is_active=True,
            is_healthy=True,
        )

    def test_create_project_with_proxy(self):
        """AC[场景8]: 创建Project时设置proxy_id"""
        project = Project.objects.create(
            name="测试项目",
            original_topic="测试主题",
            user=self.user,
            proxy_config=self.proxy,
        )

        self.assertEqual(project.proxy_config, self.proxy)
        self.assertEqual(project.proxy_config.id, self.proxy.id)

    def test_create_project_without_proxy(self):
        """AC[场景6]: 创建Project时不设置proxy_id（向后兼容）"""
        project = Project.objects.create(
            name="测试项目",
            original_topic="测试主题",
            user=self.user,
        )

        self.assertIsNone(project.proxy_config)

    def test_create_project_with_invalid_proxy(self):
        """测试创建Project时使用无效proxy_id（应报错）"""
        from django.core.exceptions import ValidationError

        # 尝试使用不存在的proxy_id
        with self.assertRaises(ValidationError):
            project = Project(
                name="测试项目",
                original_topic="测试主题",
                user=self.user,
                proxy_config_id=99999,  # 不存在的代理
            )
            project.full_clean()  # 验证模型


class ProjectModificationWithProxyTest(TestCase):
    """Phase 3: Project修改proxy_id"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        self.proxy1 = ProxyConfig.objects.create(
            name="代理1",
            protocol=ProxyProtocol.HTTP,
            host="proxy1.example.com",
            port=8080,
        )
        self.proxy2 = ProxyConfig.objects.create(
            name="代理2",
            protocol=ProxyProtocol.HTTPS,
            host="proxy2.example.com",
            port=8443,
        )

        self.project = Project.objects.create(
            name="测试项目",
            original_topic="测试主题",
            user=self.user,
            proxy_config=self.proxy1,
        )

    def test_update_project_proxy(self):
        """AC[场景8]: 更新Project的proxy_id"""
        self.project.proxy_config = self.proxy2
        self.project.save()

        self.project.refresh_from_db()
        self.assertEqual(self.project.proxy_config, self.proxy2)

    def test_remove_project_proxy(self):
        """AC[场景8]: 移除Project的proxy_id（设为NULL）"""
        self.project.proxy_config = None
        self.project.save()

        self.project.refresh_from_db()
        self.assertIsNone(self.project.proxy_config)


class CascadeDeleteTest(TestCase):
    """Phase 4: 级联删除测试（SET_NULL策略）"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        self.project = Project.objects.create(
            name="测试项目",
            original_topic="测试主题",
            user=self.user,
            proxy_config=self.proxy,
        )

    def test_delete_proxy_sets_project_proxy_to_null(self):
        """AC[场景6]: 删除代理时，Project的proxy_id设为NULL（SET_NULL策略）"""
        # 确认项目关联了代理
        self.assertEqual(self.project.proxy_config, self.proxy)

        # 删除代理
        self.proxy.delete()

        # 刷新项目
        self.project.refresh_from_db()

        # 验证项目的proxy_config设为NULL
        self.assertIsNone(self.project.proxy_config)
        # 项目仍然存在
        self.assertIsNotNone(Project.objects.filter(id=self.project.id).first())

    def test_delete_project_does_not_delete_proxy(self):
        """测试删除Project时不删除ProxyConfig"""
        proxy_id = self.proxy.id
        project_id = self.project.id

        # 删除项目
        self.project.delete()

        # 验证代理仍然存在
        self.assertIsNotNone(ProxyConfig.objects.filter(id=proxy_id).first())
        # 验证项目已删除（使用 project_id）
        self.assertIsNone(Project.objects.filter(id=project_id).first())


class ReverseRelationQueryTest(TestCase):
    """Phase 5: 反向关联查询测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        # 创建多个使用该代理的项目
        self.project1 = Project.objects.create(
            name="项目1",
            original_topic="主题1",
            user=self.user,
            proxy_config=self.proxy,
        )
        self.project2 = Project.objects.create(
            name="项目2",
            original_topic="主题2",
            user=self.user,
            proxy_config=self.proxy,
        )
        # 创建一个不使用该代理的项目
        self.project3 = Project.objects.create(
            name="项目3",
            original_topic="主题3",
            user=self.user,
        )

    def test_reverse_relation_query(self):
        """AC[场景7]: 执行proxy_config.projects.all()返回所有使用该代理的项目"""
        # 反向查询
        projects = self.proxy.projects.all()

        # 验证返回2个项目
        self.assertEqual(projects.count(), 2)
        # 验证包含正确的项目
        self.assertIn(self.project1, projects)
        self.assertIn(self.project2, projects)
        # 不包含不使用该代理的项目
        self.assertNotIn(self.project3, projects)


class APISerializationTest(TestCase):
    """Phase 6: API序列化测试"""

    def setUp(self):
        """设置测试数据"""
        self.user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        self.proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        self.project_with_proxy = Project.objects.create(
            name="有代理项目",
            original_topic="主题",
            user=self.user,
            proxy_config=self.proxy,
        )

        self.project_without_proxy = Project.objects.create(
            name="无代理项目",
            original_topic="主题",
            user=self.user,
        )

    def test_project_list_serialization_includes_proxy_id(self):
        """AC[场景4]: API返回的JSON包含proxy_id字段"""
        from apps.projects.serializers import ProjectListSerializer

        serializer = ProjectListSerializer(self.project_with_proxy)
        data = serializer.data

        # 验证包含proxy_config和proxy_name
        self.assertIn("proxy_config", data)
        self.assertIn("proxy_name", data)
        # 验证值正确
        self.assertEqual(data["proxy_config"], self.proxy.id)
        self.assertEqual(data["proxy_name"], "测试代理")

    def test_project_list_serialization_with_null_proxy(self):
        """AC[场景4]: 无代理时proxy_id为null"""
        from apps.projects.serializers import ProjectListSerializer

        serializer = ProjectListSerializer(self.project_without_proxy)
        data = serializer.data

        # 验证proxy_config为null
        self.assertIsNone(data["proxy_config"])
        self.assertIsNone(data["proxy_name"])

    def test_project_detail_serialization_includes_proxy_id(self):
        """AC[场景4]: 详情API返回的JSON包含proxy_id字段"""
        from apps.projects.serializers import ProjectDetailSerializer

        serializer = ProjectDetailSerializer(self.project_with_proxy)
        data = serializer.data

        # 验证包含proxy_config和proxy_name
        self.assertIn("proxy_config", data)
        self.assertIn("proxy_name", data)
        self.assertEqual(data["proxy_config"], self.proxy.id)
        self.assertEqual(data["proxy_name"], "测试代理")


class DjangoAdminDisplayTest(TestCase):
    """Phase 7: Django Admin显示测试"""

    def test_admin_config_includes_proxy_config(self):
        """AC[场景3]: Django Admin显示代理配置字段"""
        from apps.projects.admin import ProjectAdmin

        # 验证list_display包含proxy_config
        self.assertIn("proxy_config", ProjectAdmin.list_display)
        # 验证list_filter包含proxy_config
        self.assertIn("proxy_config", ProjectAdmin.list_filter)

    def test_admin_fieldsets_includes_proxy_config(self):
        """AC[场景3]: Django Admin fieldsets包含代理配置"""
        from apps.projects.admin import ProjectAdmin

        # 验证fieldsets包含proxy_config
        fieldsets = ProjectAdmin.fieldsets
        config_fieldset = fieldsets[1]  # 配置fieldset
        self.assertIn("proxy_config", config_fieldset[1]["fields"])


class BackwardCompatibilityTest(TestCase):
    """Phase 8: 向后兼容性测试"""

    def test_existing_projects_work_without_proxy(self):
        """AC[场景5]: 现有Project数据不受影响"""
        from apps.projects.serializers import ProjectListSerializer

        user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )
        project = Project.objects.create(
            name="老项目",
            original_topic="主题",
            user=user,
            # 不设置proxy_config
        )

        # 验证序列化正常工作
        serializer = ProjectListSerializer(project)
        data = serializer.data

        self.assertIn("proxy_config", data)
        self.assertIsNone(data["proxy_config"])
        self.assertIn("proxy_name", data)
        self.assertIsNone(data["proxy_name"])

    def test_query_projects_without_filtering_proxy(self):
        """测试查询Project时不需要过滤proxy_config"""
        user = User.objects.create_user(
            username=f"testuser_{uuid.uuid4().hex[:8]}", password="testpass"
        )

        # 创建多个项目（有代理和无代理）
        proxy = ProxyConfig.objects.create(
            name="测试代理",
            protocol=ProxyProtocol.HTTP,
            host="proxy.example.com",
            port=8080,
        )

        project1 = Project.objects.create(
            name="项目1",
            original_topic="主题1",
            user=user,
            proxy_config=proxy,
        )
        project2 = Project.objects.create(
            name="项目2",
            original_topic="主题2",
            user=user,
        )

        # 查询该用户的项目
        projects = Project.objects.filter(user=user)

        # 验证查询正常工作
        self.assertEqual(projects.count(), 2)
        self.assertIn(project1, projects)
        self.assertIn(project2, projects)
