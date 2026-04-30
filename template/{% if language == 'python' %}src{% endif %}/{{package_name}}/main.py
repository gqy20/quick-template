"""{{package_name }} 应用程序的主入口"""

import asyncio
from pydantic import BaseModel, Field

from rich.panel import Panel
from rich.table import Table

from {{package_name}}.core import add, greet
from {{package_name}}.logger import console, logger, print_header, print_success

# Agent SDK 模块可选导入
try:
    from {{package_name}}.agent import (
        AgentRunner,
        output_format_schema,
        sentiment_schema,
        code_review_schema,
        structured_query,
    )
    HAS_AGENT_SDK = True
except ImportError:
    HAS_AGENT_SDK = False


def demo_basic_features() -> None:
    """演示基本功能"""
    print_header("基本功能演示")

    # 测试问候函数
    message = greet("Python 开发者")
    print_success(f"问候: {message}")

    # 测试加法函数
    result = add(10, 20)
    print_success(f"加法: 10 + 20 = {result}")


def demo_rich_output() -> None:
    """演示 Rich 格式化功能"""
    print_header("Rich 输出演示")

    # 创建表格
    table = Table(title="功能对比")
    table.add_column("功能", style="cyan", no_wrap=True)
    table.add_column("状态", style="magenta")
    table.add_column("描述", style="green")

    table.add_row("日志", "✓", "Rich 格式化日志，支持文件输出")
    table.add_row("测试", "✓", "pytest，100% 覆盖率")
    table.add_row("代码检查", "✓", "ruff")
    table.add_row("CI/CD", "✓", "GitHub Actions 自动化")
    if HAS_AGENT_SDK:
        table.add_row("Agent SDK", "✓", "Claude Agent SDK 结构化输出")

    console.print(table)


def demo_logging() -> None:
    """演示日志功能"""
    print_header("日志演示")

    logger.debug("这是一条调试消息")
    logger.info("这是一条信息消息")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")

    console.print(
        Panel(
            "[bold green]日志已保存到 logs/{{project_slug }}.log[/bold green]",
            title="日志文件位置",
            border_style="blue",
        )
    )


# ============================================================================
# Agent SDK 结构化输出演示
# ============================================================================


class SentimentOutput(BaseModel):
    """情感分析输出模型。"""
    sentiment: str = Field(description="情感倾向: positive/negative/neutral")
    confidence: float = Field(description="置信度 0-1")
    keywords: list[str] = Field(description="关键词列表")


class CodeIssue(BaseModel):
    """代码问题。"""
    severity: str = Field(description="严重程度: critical/major/minor/info")
    line: int | None = Field(default=None, description="行号")
    description: str = Field(description="问题描述")
    suggestion: str | None = Field(default=None, description="修复建议")


class CodeReviewOutput(BaseModel):
    """代码审查输出模型。"""
    score: int = Field(description="代码评分 0-10", ge=0, le=10)
    issues: list[CodeIssue] = Field(default_factory=list, description="问题列表")
    overall: str = Field(description="总体评价")


async def demo_agent_sentiment() -> None:
    """演示 Agent SDK 结构化输出 — 情感分析。

    数据流（基于 SDK 源码分析）：
        prompt → query() → [StreamEvent, AssistantMessage] → ResultMessage
                                                    ↓
                                          ResultMessage.structured_output (dict)
                                                    ↓
                                          parse_with_model() → SentimentOutput
    """
    if not HAS_AGENT_SDK:
        console.print("[yellow]跳过: claude-agent-sdk 未安装[/yellow]")
        return

    print_header("Agent SDK — 结构化输出（情感分析）")

    schema = output_format_schema(SentimentOutput)
    console.print(f"[dim]Schema: {schema['name']}[/dim]\n")

    runner = AgentRunner(
        schema=schema,
        system_prompt="你是一个专业的情感分析专家。分析给定文本的情感倾向。",
        max_turns=1,
    )

    console.print("[cyan]查询: 分析「这个产品太棒了！物流很快，客服也很耐心。」[/cyan]\n")
    result = await runner.run(
        "分析以下文本的情感倾向：这个产品太棒了！物流很快，客服也很耐心。",
        SentimentOutput,
    )

    if result:
        console.print("\n[bold green]=== 结构化输出结果 ===[/bold green]")
        console.print(f"  情感倾向: [cyan]{result.sentiment}[/cyan]")
        console.print(f"  置信度:   [cyan]{result.confidence:.2f}[/cyan]")
        console.print(f"  关键词:   [cyan]{', '.join(result.keywords)}[/cyan]")
        print_success("情感分析完成！")
    else:
        console.print("[red]未能获取结构化输出[/red]")


async def demo_agent_code_review() -> None:
    """演示 Agent SDK 结构化输出 — 代码审查。

    使用预定义 Schema 工厂 + AgentRunner。
    """
    if not HAS_AGENT_SDK:
        console.print("[yellow]跳过: claude-agent-sdk 未安装[/yellow]")
        return

    print_header("Agent SDK — 结构化输出（代码审查）")

    sample_code = '''def calc(x, y):
    return x+y

def process(data):
    results = []
    for i in data:
        results.append(calc(i, i*2))
    return results'''

    console.print(f"[dim]待审查代码:[/dim]\n[dim]{sample_code}[/dim]\n")

    # 使用预定义 Schema 工厂
    schema = code_review_schema()
    console.print(f"[dim]Schema: {schema['name']}[/dim]\n")

    runner = AgentRunner(
        schema=schema,
        system_prompt="你是一个资深代码审查专家。从可读性、性能、规范三个维度审查代码。",
        max_turns=2,
    )

    console.print("[cyan]正在审查代码...[/cyan]\n")
    result = await runner.run(
        f"请审查以下 Python 代码的质量，给出评分和具体问题：\n\n{sample_code}",
        CodeReviewOutput,
    )

    if result:
        console.print("\n[bold green]=== 审查结果 ===[/bold green]")
        console.print(f"  评分:     [cyan]{result.score}/10[/cyan]")
        console.print(f"  总体评价: {result.overall}\n")

        if result.issues:
            issue_table = Table(title="发现的问题")
            issue_table.add_column("严重度", style="red")
            issue_table.add_column("行号", style="yellow")
            issue_table.add_column("描述")
            issue_table.add_column("建议", style="green")

            for issue in result.issues:
                issue_table.add_row(
                    issue.severity,
                    str(issue.line) if issue.line else "-",
                    issue.description,
                    issue.suggestion or "-",
                )
            console.print(issue_table)
        else:
            console.print("[green]未发现问题[/green]")

        print_success("代码审查完成！")
    else:
        console.print("[red]未能获取结构化输出[/red]")


async def demo_agent_quick_query() -> None:
    """演示 structured_query 快捷函数（一行调用）。"""
    if not HAS_AGENT_SDK:
        console.print("[yellow]跳过: claude-agent-sdk 未安装[/yellow]")
        return

    print_header("Agent SDK — 快捷结构化查询")

    class SummaryOutput(BaseModel):
        title: str = Field(description="标题")
        points: list[str] = Field(description="要点列表")
        word_count: int = Field(description="原文字数估计")

    console.print("[cyan]使用 structured_query() 一行调用[/cyan]\n")
    result = await structured_query(
        "用一句话总结 Python 的特点，并列出 3 个核心优势",
        SummaryOutput,
        system_prompt="你是一个技术文档撰写专家。",
        max_turns=1,
    )

    if result:
        console.print(f"\n[bold green]标题:[/bold green] {result.title}")
        for i, point in enumerate(result.points, 1):
            console.print(f"  [cyan]{i}.[/cyan] {point}")
        console.print(f"\n[dim]估计字数: {result.word_count}[/dim]")
        print_success("快捷查询完成！")
    else:
        console.print("[red]未能获取结果[/red]")


# ============================================================================
# 主程序
# ============================================================================


async def run_agent_demos() -> None:
    """运行所有 Agent SDK 演示（异步）。"""
    if not HAS_AGENT_SDK:
        console.print("[yellow]Agent SDK 演示已跳过（claude-agent-sdk 未安装）[/yellow]\n")
        return

    await demo_agent_sentiment()
    console.print()
    await demo_agent_code_review()
    console.print()
    await demo_agent_quick_query()


def main() -> None:
    """运行主程序"""
    console.print(
        Panel.fit(
            "[bold cyan]{{project_name }}[/bold cyan] - {{description }}",
            border_style="cyan",
        )
    )

    logger.info("应用程序已启动")

    try:
        # 同步演示
        demo_basic_features()
        console.print()
        demo_rich_output()
        console.print()
        demo_logging()

        # 异步 Agent SDK 演示
        if HAS_AGENT_SDK:
            console.print()
            asyncio.run(run_agent_demos())

        logger.info("应用程序成功完成")
        print_success("所有演示已完成！")

    except Exception as e:
        logger.error(f"应用程序错误: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
