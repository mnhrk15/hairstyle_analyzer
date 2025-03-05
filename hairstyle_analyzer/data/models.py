"""
データモデル定義モジュール

このモジュールでは、アプリケーション全体で使用するデータモデルを定義します。
Pydanticを使用して、データの検証と型安全性を確保します。
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class StyleFeatures(BaseModel):
    """スタイルの特徴を表すモデル"""
    color: str = Field(description="髪色の詳細説明")
    cut_technique: str = Field(description="カット技法の詳細")
    styling: str = Field(description="スタイリング方法")
    impression: str = Field(description="全体的な印象")


class StyleAnalysis(BaseModel):
    """スタイル分析結果を表すモデル"""
    category: str = Field(description="スタイルのカテゴリ")
    features: StyleFeatures = Field(description="スタイルの特徴")
    keywords: List[str] = Field(default_factory=list, description="スタイルのキーワードリスト")


class AttributeAnalysis(BaseModel):
    """属性分析結果を表すモデル"""
    sex: str = Field(description="性別（レディース/メンズ）")
    length: str = Field(description="髪の長さ")


class Template(BaseModel):
    """テンプレートを表すモデル"""
    category: str = Field(description="スタイルカテゴリ")
    title: str = Field(description="スタイルタイトル")
    menu: str = Field(description="スタイルメニュー")
    comment: str = Field(description="スタイルコメント")
    hashtag: str = Field(description="ハッシュタグ（カンマ区切り）")
    
    def get_hashtags(self) -> List[str]:
        """
        ハッシュタグリストを取得します。
        
        Returns:
            ハッシュタグのリスト
        """
        if not self.hashtag:
            return []
        return [tag.strip() for tag in self.hashtag.split(',') if tag.strip()]


class StylistInfo(BaseModel):
    """スタイリスト情報を表すモデル"""
    name: str = Field(description="スタイリスト名")
    specialties: str = Field(description="得意な技術・特徴")
    description: str = Field(description="説明文")


class CouponInfo(BaseModel):
    """
    クーポン情報を表すモデル
    """
    name: str
    price: int
    description: str
    categories: List[str] = Field(default_factory=list)
    conditions: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        frozen = True


class ProcessResult(BaseModel):
    """処理結果を表すモデル"""
    image_name: str = Field(description="画像ファイル名")
    style_analysis: StyleAnalysis = Field(description="スタイル分析結果")
    attribute_analysis: AttributeAnalysis = Field(description="属性分析結果")
    selected_template: Template = Field(description="選択されたテンプレート")
    selected_stylist: StylistInfo = Field(description="選択されたスタイリスト")
    selected_coupon: CouponInfo = Field(description="選択されたクーポン")
    processed_at: datetime = Field(default_factory=datetime.now, description="処理日時")
    stylist_reason: Optional[str] = Field(default=None, description="スタイリスト選択理由")
    coupon_reason: Optional[str] = Field(default=None, description="クーポン選択理由")


class CacheEntry(BaseModel):
    """キャッシュエントリーを表すモデル"""
    data: Any = Field(description="キャッシュデータ")
    timestamp: float = Field(description="作成タイムスタンプ")
    ttl: Optional[float] = Field(default=None, description="有効期限（秒単位）")


class GeminiConfig(BaseModel):
    """Gemini API設定を表すモデル"""
    api_key: str = Field(description="Gemini API Key")
    model: str = Field(default="gemini-2.0-flash", description="使用するGeminiモデル")
    fallback_model: str = Field(default="gemini-2.0-flash-lite", description="フォールバックモデル")
    max_tokens: int = Field(default=300, description="生成する最大トークン数")
    temperature: float = Field(default=0.7, description="生成の温度パラメータ")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: float = Field(default=1.0, description="リトライ間隔（秒）")
    prompt_template: str = Field(description="プロンプトテンプレート")
    attribute_prompt_template: str = Field(description="属性分析用プロンプトテンプレート")
    stylist_prompt_template: str = Field(description="スタイリスト選択用プロンプトテンプレート")
    coupon_prompt_template: str = Field(description="クーポン選択用プロンプトテンプレート")
    length_choices: List[str] = Field(description="髪の長さの選択肢リスト")


class ScraperConfig(BaseModel):
    """スクレイパー設定を表すモデル"""
    base_url: str = Field(description="スクレイピング対象のベースURL")
    stylist_link_selector: str = Field(description="スタイリストリンクのセレクタ")
    stylist_name_selector: str = Field(description="スタイリスト名のセレクタ")
    stylist_description_selector: str = Field(description="スタイリスト説明のセレクタ")
    coupon_class_name: str = Field(default="couponMenuName", description="クーポン名のクラス名")
    coupon_page_parameter_name: str = Field(default="PN", description="クーポンページパラメータ名")
    coupon_page_start_number: int = Field(default=2, description="クーポンページ開始番号")
    coupon_page_limit: int = Field(default=3, description="クーポンページ数上限")
    timeout: int = Field(default=10, description="リクエストタイムアウト（秒）")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: int = Field(default=1, description="リトライ間隔（秒）")


class ExcelConfig(BaseModel):
    """Excel出力設定を表すモデル"""
    headers: Dict[str, str] = Field(description="Excel出力のヘッダー定義")


class ProcessingConfig(BaseModel):
    """処理設定を表すモデル"""
    batch_size: int = Field(default=5, description="バッチサイズ")
    api_delay: float = Field(default=1.0, description="API呼び出し間の遅延（秒）")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: float = Field(default=1.0, description="リトライ間隔（秒）")
    memory_per_image_mb: int = Field(default=5, description="画像あたりのメモリ使用量（MB）")


class PathsConfig(BaseModel):
    """パス設定を表すモデル"""
    image_folder: Path = Field(description="画像フォルダのパス")
    template_csv: Path = Field(description="テンプレートCSVファイルのパス")
    output_excel: Path = Field(description="出力Excelファイルのパス")
    cache_file: Path = Field(description="キャッシュファイルのパス")
    log_file: Path = Field(description="ログファイルのパス")


class CacheConfig(BaseModel):
    """キャッシュ設定を表すモデル"""
    ttl_days: int = Field(default=30, description="キャッシュの有効期限（日数）")
    max_size: int = Field(default=10000, description="最大キャッシュエントリ数")


class LoggingConfig(BaseModel):
    """ロギング設定を表すモデル"""
    log_file: Path = Field(description="ログファイルのパス")
    log_level: str = Field(default="INFO", description="ログレベル")


class AppConfig(BaseModel):
    """アプリケーション全体の設定を表すモデル"""
    gemini: GeminiConfig = Field(description="Gemini API設定")
    scraper: ScraperConfig = Field(description="スクレイパー設定")
    excel: ExcelConfig = Field(description="Excel出力設定")
    processing: ProcessingConfig = Field(description="処理設定")
    paths: PathsConfig = Field(description="パス設定")
    cache: CacheConfig = Field(description="キャッシュ設定")
    logging: LoggingConfig = Field(description="ロギング設定")
