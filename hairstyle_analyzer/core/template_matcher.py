"""
テンプレートマッチングモジュール

このモジュールでは、画像分析結果に基づいて最適なテンプレートを選択するための機能を提供します。
カテゴリマッチング、特徴ベースのスコアリング、最適テンプレート選択ロジックが含まれます。
"""

import logging
import difflib
from typing import List, Optional, Dict, Any, Tuple, Set

from ..data.models import Template, StyleAnalysis, StyleFeatures
from ..data.interfaces import StyleAnalysisProtocol, TemplateManagerProtocol
from ..utils.errors import TemplateError, with_error_handling


class TemplateMatcher:
    """
    テンプレートマッチングクラス
    
    画像分析結果に基づいて最適なテンプレートを選択します。
    カテゴリマッチング、特徴ベースのスコアリング、キーワード類似度計算などの機能が含まれます。
    """
    
    def __init__(self, template_manager: TemplateManagerProtocol):
        """
        初期化
        
        Args:
            template_manager: テンプレートマネージャー
        """
        self.logger = logging.getLogger(__name__)
        self.template_manager = template_manager
    
    @with_error_handling(TemplateError, "テンプレートマッチング処理でエラーが発生しました")
    def find_best_template(self, analysis: StyleAnalysisProtocol) -> Optional[Template]:
        """
        分析結果に最適なテンプレートを検索します。
        
        Args:
            analysis: 画像分析結果
            
        Returns:
            最適なテンプレート、見つからない場合はNone
            
        Raises:
            TemplateError: テンプレート処理中にエラーが発生した場合
        """
        # 辞書型の場合はStyleAnalysisに変換
        if isinstance(analysis, dict):
            try:
                features = StyleFeatures(**analysis.get('features', {}))
                analysis = StyleAnalysis(
                    category=analysis.get('category', ''),
                    features=features,
                    keywords=analysis.get('keywords', [])
                )
            except Exception as e:
                self.logger.error(f"分析結果の変換に失敗しました: {e}")
                raise TemplateError(f"分析結果の変換に失敗: {str(e)}")
        
        self.logger.info(f"テンプレートマッチング開始: カテゴリ={analysis.category}")
        
        # テンプレートマネージャーを使用して最適なテンプレートを検索
        template = self.template_manager.find_best_template(analysis)
        
        if template:
            self.logger.info(f"最適なテンプレートを見つけました: タイトル={template.title}")
        else:
            self.logger.warning(f"適切なテンプレートが見つかりませんでした")
            
        return template
    
    def find_alternative_templates(self, analysis: StyleAnalysisProtocol, count: int = 3) -> List[Template]:
        """
        代替テンプレートを検索します。
        
        Args:
            analysis: 画像分析結果
            count: 返す代替テンプレートの数
            
        Returns:
            代替テンプレートのリスト
        """
        self.logger.info(f"代替テンプレート検索開始: カテゴリ={analysis.category}")
        
        templates = []
        
        # まず分析結果のカテゴリに一致するテンプレートを取得
        category_templates = self.template_manager.get_templates_by_category(analysis.category)
        
        # 一致するカテゴリがない場合、全テンプレートを対象にする
        if not category_templates:
            category_templates = self.template_manager.get_all_templates()
        
        # 十分なテンプレートがある場合は、分析結果のキーワードや特徴に基づいてスコアリング
        if len(category_templates) > 1:
            # スコアリングロジックの実装
            scored_templates = self._score_templates(category_templates, analysis)
            
            # 結果をスコア降順にソート
            scored_templates.sort(key=lambda x: x[0], reverse=True)
            
            # 上位のテンプレートを返す（最良のテンプレートを除く）
            templates = [template for score, template in scored_templates[:count+1]]
            
            # 既に find_best_template で最良のテンプレートが返されている可能性があるため、
            # リストが十分な長さの場合は最初のテンプレートを除外
            if len(templates) > count:
                templates = templates[1:count+1]
        else:
            templates = category_templates[:count]
        
        return templates
    
    def _score_templates(self, templates: List[Template], analysis: StyleAnalysisProtocol) -> List[Tuple[float, Template]]:
        """
        テンプレートをスコアリングします。
        
        Args:
            templates: スコアリングするテンプレートのリスト
            analysis: 画像分析結果
            
        Returns:
            (スコア, テンプレート) のタプルのリスト
        """
        scored_templates = []
        
        # 分析結果からキーワードを取得
        analysis_keywords = set(analysis.keywords)
        
        for template in templates:
            score = 0.0
            
            # カテゴリの一致（最も重要）
            if template.category == analysis.category:
                score += 3.0
            
            # キーワードの一致（2番目に重要）
            template_tags = set(template.get_hashtags())
            if template_tags and analysis_keywords:
                # 共通するキーワードの割合
                common_keywords = template_tags.intersection(analysis_keywords)
                keyword_score = len(common_keywords) / max(len(template_tags), 1) * 2.0
                score += keyword_score
            
            # テキスト内容の類似度（3番目に重要）
            # タイトル、コメント、メニューなどのテキスト内容に分析結果の特徴が含まれているかを評価
            combined_text = f"{template.title} {template.comment} {template.menu}".lower()
            
            # 特徴値のリスト
            features_values = [
                analysis.features.color,
                analysis.features.cut_technique,
                analysis.features.styling,
                analysis.features.impression
            ]
            
            # 各特徴についてテキスト内での一致を評価
            for feature_value in features_values:
                if feature_value.lower() in combined_text:
                    score += 0.5
            
            scored_templates.append((score, template))
        
        return scored_templates
    
    def get_template_by_category(self, category: str) -> Optional[Template]:
        """
        指定されたカテゴリから最初のテンプレートを取得します。
        
        Args:
            category: カテゴリ名
            
        Returns:
            テンプレート、見つからない場合はNone
        """
        templates = self.template_manager.get_templates_by_category(category)
        if templates:
            return templates[0]
        return None
    
    def get_random_template(self) -> Optional[Template]:
        """
        ランダムなテンプレートを取得します。
        
        Returns:
            テンプレート、見つからない場合はNone
        """
        import random
        templates = self.template_manager.get_all_templates()
        if templates:
            return random.choice(templates)
        return None
