"""
项目管理序列化器
职责: 数据序列化与验证
遵循单一职责原则(SRP)
"""

import contextlib

from rest_framework import serializers

from apps.projects.utils import parse_storyboard_json

from .models import Project, ProjectModelConfig, ProjectStage, ProjectTemplate


class ProjectStageSerializer(serializers.ModelSerializer):
    """项目阶段序列化器"""

    stage_type_display = serializers.CharField(source="get_stage_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProjectStage
        fields = [
            "id",
            "project",
            "stage_type",
            "stage_type_display",
            "status",
            "status_display",
            "input_data",
            "output_data",
            "retry_count",
            "max_retries",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "started_at", "completed_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        stage_type = data.get("stage_type")
        if stage_type == "storyboard":
            with contextlib.suppress(Exception):
                data["output_data"]["human_text"] = parse_storyboard_json(
                    data["output_data"].get("storyboard_text", "")
                )
        elif stage_type == "image_generation":
            with contextlib.suppress(Exception):
                data["input_data"]["human_text"] = parse_storyboard_json(
                    data["input_data"].get("storyboard_text", "")
                )
        return data


class ProjectModelConfigSerializer(serializers.ModelSerializer):
    """项目模型配置序列化器"""

    load_balance_strategy_display = serializers.CharField(
        source="get_load_balance_strategy_display", read_only=True
    )

    # 显示模型提供商名称列表
    rewrite_providers_names = serializers.SerializerMethodField()
    storyboard_providers_names = serializers.SerializerMethodField()
    image_providers_names = serializers.SerializerMethodField()
    camera_providers_names = serializers.SerializerMethodField()
    video_providers_names = serializers.SerializerMethodField()

    class Meta:
        model = ProjectModelConfig
        fields = [
            "id",
            "project",
            "load_balance_strategy",
            "load_balance_strategy_display",
            "rewrite_providers",
            "rewrite_providers_names",
            "storyboard_providers",
            "storyboard_providers_names",
            "image_providers",
            "image_providers_names",
            "camera_providers",
            "camera_providers_names",
            "video_providers",
            "video_providers_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_rewrite_providers_names(self, obj):
        return [p.name for p in obj.rewrite_providers.all()]

    def get_storyboard_providers_names(self, obj):
        return [p.name for p in obj.storyboard_providers.all()]

    def get_image_providers_names(self, obj):
        return [p.name for p in obj.image_providers.all()]

    def get_camera_providers_names(self, obj):
        return [p.name for p in obj.camera_providers.all()]

    def get_video_providers_names(self, obj):
        return [p.name for p in obj.video_providers.all()]


class ProjectListSerializer(serializers.ModelSerializer):
    """项目列表序列化器 - 轻量级"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    prompt_set_name = serializers.CharField(source="prompt_template_set.name", read_only=True)
    proxy_name = serializers.CharField(source="proxy_config.name", read_only=True, allow_null=True)

    # Epic 12: 关联作品ID
    artwork_id = serializers.PrimaryKeyRelatedField(source="artwork.id", read_only=True, allow_null=True)

    # 统计信息
    stages_count = serializers.SerializerMethodField()
    completed_stages_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "artwork_id",
            "name",
            "description",
            "original_topic",
            "status",
            "status_display",
            "user",
            "user_name",
            "prompt_template_set",
            "prompt_set_name",
            "proxy_config",
            "proxy_name",
            "stages_count",
            "completed_stages_count",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "completed_at"]

    def get_stages_count(self, obj):
        return obj.stages.count()

    def get_completed_stages_count(self, obj):
        return obj.stages.filter(status="completed").count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    """项目详情序列化器 - 包含完整信息"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    prompt_set_name = serializers.CharField(source="prompt_template_set.name", read_only=True)
    proxy_name = serializers.CharField(source="proxy_config.name", read_only=True, allow_null=True)

    # Epic 12: 关联作品ID
    artwork_id = serializers.PrimaryKeyRelatedField(source="artwork.id", read_only=True, allow_null=True)

    # 嵌套序列化
    stages = ProjectStageSerializer(many=True, read_only=True)
    model_config = ProjectModelConfigSerializer(read_only=True)

    # 统计信息
    total_stages = serializers.SerializerMethodField()
    completed_stages = serializers.SerializerMethodField()
    failed_stages = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "artwork_id",
            "description",
            "original_topic",
            "status",
            "status_display",
            "user",
            "user_name",
            "prompt_template_set",
            "prompt_set_name",
            "proxy_config",
            "proxy_name",
            "stages",
            "model_config",
            "total_stages",
            "completed_stages",
            "failed_stages",
            "progress_percentage",
            "created_at",
            "updated_at",
            "completed_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "completed_at"]

    def get_total_stages(self, obj):
        return obj.stages.count()

    def get_completed_stages(self, obj):
        return obj.stages.filter(status="completed").count()

    def get_failed_stages(self, obj):
        return obj.stages.filter(status="failed").count()

    def get_progress_percentage(self, obj):
        total = obj.stages.count()
        if total == 0:
            return 0
        completed = obj.stages.filter(status="completed").count()
        return round((completed / total) * 100, 2)


class ProjectCreateSerializer(serializers.ModelSerializer):
    """项目创建序列化器"""

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "original_topic",
            "prompt_template_set",
            "proxy_config",
        ]
        read_only_fields = ["id"]

    def validate_original_topic(self, value):
        """验证原始主题不能为空"""
        if not value or not value.strip():
            raise serializers.ValidationError("原始主题不能为空")
        return value.strip()

    def create(self, validated_data):
        """创建项目并初始化阶段"""
        # 从请求中获取用户
        user = self.context["request"].user
        validated_data["user"] = user

        # 创建项目
        project = Project.objects.create(**validated_data)

        # 初始化5个阶段
        for stage_type in ["rewrite", "storyboard"]:
            ProjectStage.objects.create(
                project=project,
                stage_type=stage_type,
                status="pending",
                input_data={"raw_text": project.original_topic, "human_text": ""},
                output_data={"raw_text": "", "human_text": ""},
            )
        stage_types = ["image_generation", "camera_movement", "video_generation"]
        for stage_type in stage_types:
            ProjectStage.objects.create(
                project=project,
                stage_type=stage_type,
                status="pending",
                input_data={"raw_text": "", "human_text": ""},
                output_data={"raw_text": "", "human_text": ""},
            )

        # 创建默认模型配置
        ProjectModelConfig.objects.create(project=project)

        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """项目更新序列化器"""

    class Meta:
        model = Project
        fields = ["name", "description", "original_topic", "prompt_template_set", "status"]

    def validate_status(self, value):
        """验证状态转换的合法性"""
        instance = self.instance
        if instance:
            # 已完成的项目不能修改为其他状态
            if instance.status == "completed" and value != "completed":
                raise serializers.ValidationError("已完成的项目不能修改状态")

            # 只有暂停和草稿状态可以恢复处理
            if value == "processing" and instance.status not in ["paused", "draft"]:
                raise serializers.ValidationError(
                    f"项目状态为 {instance.get_status_display()} 时不能开始处理"
                )

        return value


class StageRetrySerializer(serializers.Serializer):
    """阶段重试序列化器"""

    stage_name = serializers.ChoiceField(
        choices=["rewrite", "storyboard", "image_generation", "camera_movement", "video_generation"]
    )

    def validate_stage_name(self, value):
        """验证阶段是否存在且可重试"""
        project_id = self.context.get("project_id")
        if not project_id:
            raise serializers.ValidationError("缺少项目ID")

        try:
            stage = ProjectStage.objects.get(project_id=project_id, stage_type=value)
        except ProjectStage.DoesNotExist:
            raise serializers.ValidationError(f"阶段 {value} 不存在")

        # 检查重试次数
        if stage.retry_count >= stage.max_retries:
            raise serializers.ValidationError(
                f"阶段 {value} 已达到最大重试次数 ({stage.max_retries})"
            )

        return value


class StageExecuteSerializer(serializers.Serializer):
    """阶段执行序列化器"""

    stage_name = serializers.ChoiceField(
        choices=["rewrite", "storyboard", "image_generation", "camera_movement", "video_generation"]
    )
    input_data = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        """验证阶段执行的前置条件"""
        project_id = self.context.get("project_id")
        stage_name = attrs["stage_name"]

        if not project_id:
            raise serializers.ValidationError("缺少项目ID")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise serializers.ValidationError("项目不存在")

        # 检查项目状态
        if project.status not in ["draft", "processing", "paused"]:
            raise serializers.ValidationError(
                f"项目状态为 {project.get_status_display()} 时不能执行阶段"
            )

        # 检查阶段是否存在
        try:
            ProjectStage.objects.get(project_id=project_id, stage_type=stage_name)
        except ProjectStage.DoesNotExist:
            raise serializers.ValidationError(f"阶段 {stage_name} 不存在")

        # 检查阶段状态
        # if stage.status == 'processing':
        #     raise serializers.ValidationError(f"阶段 {stage_name} 正在处理中")

        return attrs


class ProjectTemplateSerializer(serializers.Serializer):
    """项目模板序列化器"""

    template_name = serializers.CharField(max_length=255)
    include_model_config = serializers.BooleanField(default=True)

    def validate_template_name(self, value):
        """验证模板名称"""
        if not value or not value.strip():
            raise serializers.ValidationError("模板名称不能为空")
        return value.strip()


class ProjectTemplateCRUDSerializer(serializers.ModelSerializer):
    """
    Story 11.4.3: 项目模板CRUD序列化器
    """

    created_by_name = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = ProjectTemplate
        fields = [
            "id",
            "name",
            "description",
            "parameters",
            "is_system_template",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_system_template",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def validate_parameters(self, value):
        """验证参数JSON格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("参数必须是JSON对象格式")

        # 验证可选的参数字段
        valid_keys = {
            "style",
            "quality",
            "aspect_ratio",
            "llm_provider",
            "image_provider",
            "video_provider",
            "prompt_template_set",
            "proxy_config",
        }
        for key in value:
            if key not in valid_keys:
                raise serializers.ValidationError(f"无效的参数键: {key}")

        return value

    def validate(self, attrs):
        """验证模板创建权限"""
        # 系统预置模板只能通过数据库迁移或管理命令创建
        if attrs.get("is_system_template", False):
            raise serializers.ValidationError("不允许直接创建系统预置模板")
        return attrs

    def create(self, validated_data):
        """创建模板时自动设置创建者"""
        user = self.context["request"].user
        validated_data["created_by"] = user
        return super().create(validated_data)
