"""
画质管理器，处理画质选择和降级逻辑
"""
from typing import Dict, List, Tuple, Optional
from logger import logger
from config import QUALITY_OPTIONS, QUALITY_MAP

class QualityManager:
    """画质管理器类"""
    
    @staticmethod
    def get_quality_code(quality_name: str) -> int:
        """
        获取画质名称对应的代码
        
        Args:
            quality_name: 画质名称 (ultra, superhigh等)
            
        Returns:
            int: 画质代码
        """
        if quality_name in QUALITY_OPTIONS:
            return QUALITY_OPTIONS[quality_name]["code"]
        # 默认返回1080P
        return 80
    
    @staticmethod
    def get_quality_name(quality_code: int) -> str:
        """
        获取画质代码对应的描述
        
        Args:
            quality_code: 画质代码
            
        Returns:
            str: 画质描述
        """
        return QUALITY_MAP.get(quality_code, f"未知画质({quality_code})")
    
    @staticmethod
    def check_degradation(requested_quality: str, available_qualities: List[int], 
                         has_vip: bool) -> Tuple[int, Optional[Dict]]:
        """
        检查是否需要画质降级，并返回最佳画质
        
        Args:
            requested_quality: 请求的画质名称
            available_qualities: 可用的画质代码列表
            has_vip: 是否有大会员权限
            
        Returns:
            Tuple[int, Optional[Dict]]: (最佳画质代码, 降级信息或None)
        """
        # 获取请求的画质代码
        requested_code = QualityManager.get_quality_code(requested_quality)
        requested_desc = QualityManager.get_quality_name(requested_code)
        
        # 检查是否需要VIP
        requires_vip = QUALITY_OPTIONS.get(requested_quality, {}).get("requires_vip", False)
        
        # 记录请求详情
        logger.debug(f"请求画质: {requested_quality} ({requested_code}), 是否需要会员: {requires_vip}")
        logger.debug(f"用户拥有会员权限: {has_vip}")
        logger.debug(f"可用画质列表: {available_qualities}")
        
        # 如果需要VIP但用户没有VIP，需要降级
        if requires_vip and not has_vip:
            # 找到不需要VIP的最高画质
            non_vip_qualities = [q for q in available_qualities if q <= 80]  # 80是1080P，不需要会员
            if non_vip_qualities:
                best_code = max(non_vip_qualities)
                best_desc = QualityManager.get_quality_name(best_code)
                
                # 构建降级信息
                degradation_info = {
                    "requested_code": requested_code,
                    "requested_name": requested_desc,
                    "current_code": best_code,
                    "current_name": best_desc,
                    "reason": "该画质需要大会员权限"
                }
                
                logger.info(f"画质降级: {requested_desc} -> {best_desc} (需要会员权限)")
                return best_code, degradation_info
        
        # 如果请求的画质不在可用列表中，降级到可用的最高画质
        if requested_code not in available_qualities:
            # 找到最接近的可用画质
            valid_qualities = sorted(available_qualities, reverse=True)
            best_code = None
            
            # 尝试找低于请求画质的最高画质
            for code in valid_qualities:
                if code <= requested_code:
                    best_code = code
                    break
            
            # 如果没找到任何低于请求画质的质量，使用可用的最高画质
            if best_code is None and valid_qualities:
                best_code = valid_qualities[0]
            
            if best_code is not None:
                best_desc = QualityManager.get_quality_name(best_code)
                
                # 构建降级信息
                degradation_info = {
                    "requested_code": requested_code,
                    "requested_name": requested_desc,
                    "current_code": best_code,
                    "current_name": best_desc,
                    "reason": "所请求的画质不可用"
                }
                
                logger.info(f"画质降级: {requested_desc} -> {best_desc} (画质不可用)")
                return best_code, degradation_info
        
        # 没有降级
        return requested_code, None
