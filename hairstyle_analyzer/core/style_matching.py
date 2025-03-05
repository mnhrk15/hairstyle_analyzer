"""
スタイルマッチングモジュール

このモジュールでは、画像分析結果に基づいて最適なスタイリストとクーポンを選択するための機能を提供します。
スタイリスト選択アルゴリズム、クーポン選択アルゴリズム、特徴と説明文の類似度計算などが含まれます。
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set

from ..data.models import StylistInfo, CouponInfo
from ..data.interfaces import StyleAnalysisProtocol, StylistInfoProtocol, CouponInfoProtocol
from ..services.gemini import GeminiService
from ..utils.errors import GeminiAPIError, ImageError, async_with_error_handling


class StyleMatchingService:
    """
    スタイルマッチングサービスクラス
    
    画像分析結果に基づいて最適なスタイリストとクーポンを選択します。
    スタイリスト選択アルゴリズム、クーポン選択アルゴリズム、特徴とテキスト間の類似度計算などの機能が含まれます。
    """
    
    def __init__(self, gemini_service: GeminiService):
        """
        初期化
        
        Args:
            gemini_service: Gemini APIサービス
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_service = gemini_service
    
    @async_with_error_handling(GeminiAPIError, "スタイリスト選択中にエラーが発生しました")
    async def select_stylist(self, image_path: Path, stylists: List[StylistInfoProtocol], 
                            analysis: StyleAnalysisProtocol) -> Tuple[Optional[StylistInfoProtocol], Optional[str]]:
        """
        画像と分析結果に基づいて最適なスタイリストを選択します。
        
        Args:
            image_path: 画像ファイルのパス
            stylists: スタイリスト情報のリスト
            analysis: 画像分析結果
            
        Returns:
            Tuple[選択されたスタイリスト, 選択理由]、見つからない場合はNone
            
        Raises:
            GeminiAPIError: API呼び出しに失敗した場合
            ImageError: 画像が無効な場合
        """
        self.logger.info(f"スタイリスト選択開始: スタイリスト数={len(stylists)}")
        
        if not stylists:
            self.logger.warning("スタイリストリストが空です")
            return None, None
        
        # Gemini APIを使用してスタイリストを選択
        try:
            selected_stylist, reason = await self.gemini_service.select_stylist(
                image_path, stylists, analysis
            )
            
            if selected_stylist:
                self.logger.info(f"スタイリストを選択しました: {selected_stylist.name}")
            else:
                self.logger.warning("スタイリストを選択できませんでした")
                # フォールバック: 最初のスタイリストを返す
                selected_stylist = stylists[0]
                reason = "スタイリストを選択できなかったため、デフォルトのスタイリストを選択しました。"
                self.logger.info(f"フォールバック: 最初のスタイリストを選択: {selected_stylist.name}")
            
            return selected_stylist, reason
            
        except Exception as e:
            self.logger.error(f"スタイリスト選択エラー: {str(e)}")
            # エラー時には最初のスタイリストをフォールバックとして返す
            if stylists:
                self.logger.info(f"エラー時のフォールバック: 最初のスタイリスト {stylists[0].name} を選択")
                return stylists[0], f"エラーが発生したため、デフォルトのスタイリストを選択しました: {str(e)}"
            return None, None
    
    @async_with_error_handling(GeminiAPIError, "クーポン選択中にエラーが発生しました")
    async def select_coupon(self, image_path: Path, coupons: List[CouponInfoProtocol], 
                           analysis: StyleAnalysisProtocol) -> Tuple[Optional[CouponInfoProtocol], Optional[str]]:
        """
        画像と分析結果に基づいて最適なクーポンを選択します。
        
        Args:
            image_path: 画像ファイルのパス
            coupons: クーポン情報のリスト
            analysis: 画像分析結果
            
        Returns:
            Tuple[選択されたクーポン, 選択理由]、見つからない場合はNone
            
        Raises:
            GeminiAPIError: API呼び出しに失敗した場合
            ImageError: 画像が無効な場合
        """
        self.logger.info(f"クーポン選択開始: クーポン数={len(coupons)}")
        
        if not coupons:
            self.logger.warning("クーポンリストが空です")
            return None, None
        
        # Gemini APIを使用してクーポンを選択
        try:
            selected_coupon, reason = await self.gemini_service.select_coupon(
                image_path, coupons, analysis
            )
            
            if selected_coupon:
                self.logger.info(f"クーポンを選択しました: {selected_coupon.name}")
            else:
                self.logger.warning("クーポンを選択できませんでした")
                # フォールバック: 最初のクーポンを返す
                selected_coupon = coupons[0]
                reason = "クーポンを選択できなかったため、デフォルトのクーポンを選択しました。"
                self.logger.info(f"フォールバック: 最初のクーポンを選択: {selected_coupon.name}")
            
            return selected_coupon, reason
            
        except Exception as e:
            self.logger.error(f"クーポン選択エラー: {str(e)}")
            # エラー時には最初のクーポンをフォールバックとして返す
            if coupons:
                self.logger.info(f"エラー時のフォールバック: 最初のクーポン {coupons[0].name} を選択")
                return coupons[0], f"エラーが発生したため、デフォルトのクーポンを選択しました: {str(e)}"
            return None, None
    
    def match_by_text_similarity(self, target_text: str, candidates: List[str]) -> int:
        """
        テキスト類似度に基づいて最適な候補のインデックスを返します。
        
        Args:
            target_text: 対象テキスト
            candidates: 候補テキストのリスト
            
        Returns:
            最適な候補のインデックス
        """
        if not candidates:
            return -1
        
        # 類似度スコアを計算
        scores = []
        for candidate in candidates:
            # difflib.SequenceMatcher を使用して類似度を計算
            import difflib
            matcher = difflib.SequenceMatcher(None, target_text.lower(), candidate.lower())
            score = matcher.ratio()
            scores.append(score)
        
        # 最大スコアのインデックスを返す
        return scores.index(max(scores))
    
    def filter_coupons_by_menu(self, coupons: List[CouponInfoProtocol], menu: str) -> List[CouponInfoProtocol]:
        """
        メニューに基づいてクーポンをフィルタリングします。
        
        Args:
            coupons: クーポン情報のリスト
            menu: メニュー名
            
        Returns:
            フィルタリングされたクーポンのリスト
        """
        filtered = []
        keywords = menu.lower().split('+')
        
        for coupon in coupons:
            coupon_name = coupon.name.lower()
            # メニューのすべてのキーワードがクーポン名に含まれているかチェック
            if all(keyword.strip() in coupon_name for keyword in keywords):
                filtered.append(coupon)
        
        # フィルタリング結果がない場合は元のリストを返す
        return filtered if filtered else coupons
