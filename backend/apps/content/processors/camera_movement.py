"""
运镜生成处理器
职责: 使用AI为每个分镜生成运镜参数
遵循单一职责原则(SRP)
"""

from apps.content.processors.llm_stage import LLMStageProcessor


class CameraMovementProcessor(LLMStageProcessor):
    """
    运镜生成阶段处理器
    为每个分镜生成适合的运镜参数

    特性:
    - 从 storyboard 阶段的 output_data 读取分镜脚本
    - 从关联的 PromptTemplate 读取提示词模板
    - 支持 Jinja2 模板渲染
    - 支持流式和非流式两种模式

    输出格式:
    生成的运镜参数应包含:
    - movement_type: 运镜类型 (static, zoom_in, pan_left, tilt_up等)
    - movement_params: 运镜参数 (speed, intensity, easing等)
    - reasoning: 选择该运镜的理由

    使用示例:
    ```python
    # 1. 非流式执行 (Pipeline自动调用)
    processor = CameraMovementProcessor()
    context = PipelineContext(project_id='xxx')
    result = await processor.process(context)

    # 2. 流式执行 (SSE推送)
    processor = CameraMovementProcessor()
    async for chunk in processor.process_stream(project_id='xxx'):
        if chunk['type'] == 'token':
            print(chunk['content'])  # 实时输出token
        elif chunk['type'] == 'done':
            print(chunk['full_text'])  # 完整运镜参数
    ```

    注意:
    后续需要添加解析器将生成的文本解析为结构化的 CameraMovement 对象
    """

    def __init__(self):
        """初始化运镜生成处理器"""
        super().__init__(stage_type="camera_movement")
