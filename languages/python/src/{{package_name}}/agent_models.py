"""可由不同 Agent Runtime 共享的结构化输出模型。"""

from pydantic import BaseModel, Field


class SentimentOutput(BaseModel):
    sentiment: str = Field(description="情感倾向: positive/negative/neutral")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1)
    keywords: list[str] = Field(description="关键词列表")


class CodeIssue(BaseModel):
    severity: str = Field(description="严重程度: critical/major/minor/info")
    line: int | None = Field(default=None, description="行号")
    description: str = Field(description="问题描述")
    suggestion: str | None = Field(default=None, description="修复建议")


class CodeReviewOutput(BaseModel):
    score: int = Field(description="代码评分 0-10", ge=0, le=10)
    issues: list[CodeIssue] = Field(default_factory=list)
    overall: str = Field(description="总体评价")


class SummaryOutput(BaseModel):
    title: str = Field(description="标题")
    points: list[str] = Field(description="要点列表")
    word_count: int = Field(description="原文字数估计", ge=0)
