#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import logging

# 简单的汉字转拼音映射表（常用汉字）
# 实际应用中可能需要更完整的映射表或使用第三方库如pypinyin
PINYIN_DICT = {
    '阿': 'a', '啊': 'a', '哎': 'ai', '唉': 'ai', '安': 'an', '按': 'an', '昂': 'ang',
    '奥': 'ao', '八': 'ba', '巴': 'ba', '白': 'bai', '百': 'bai', '班': 'ban', '半': 'ban',
    '帮': 'bang', '包': 'bao', '保': 'bao', '抱': 'bao', '报': 'bao', '暴': 'bao', '爆': 'bao',
    '杯': 'bei', '北': 'bei', '被': 'bei', '本': 'ben', '比': 'bi', '笔': 'bi', '币': 'bi',
    '必': 'bi', '毕': 'bi', '边': 'bian', '变': 'bian', '标': 'biao', '表': 'biao', '别': 'bie',
    '宾': 'bin', '冰': 'bing', '兵': 'bing', '并': 'bing', '波': 'bo', '博': 'bo', '不': 'bu',
    '步': 'bu', '部': 'bu', '才': 'cai', '采': 'cai', '彩': 'cai', '菜': 'cai', '参': 'can',
    '草': 'cao', '测': 'ce', '策': 'ce', '层': 'ceng', '曾': 'ceng', '叉': 'cha', '查': 'cha',
    '差': 'cha', '产': 'chan', '长': 'chang', '常': 'chang', '场': 'chang', '厂': 'chang', '超': 'chao',
    '车': 'che', '彻': 'che', '陈': 'chen', '称': 'chen', '成': 'cheng', '城': 'cheng', '程': 'cheng',
    '吃': 'chi', '冲': 'chong', '出': 'chu', '初': 'chu', '除': 'chu', '楚': 'chu', '处': 'chu',
    '川': 'chuan', '穿': 'chuan', '传': 'chuan', '船': 'chuan', '窗': 'chuang', '创': 'chuang', '春': 'chun',
    '词': 'ci', '此': 'ci', '次': 'ci', '从': 'cong', '村': 'cun', '存': 'cun', '错': 'cuo',
    '答': 'da', '打': 'da', '大': 'da', '代': 'dai', '带': 'dai', '单': 'dan', '但': 'dan',
    '当': 'dang', '档': 'dang', '到': 'dao', '道': 'dao', '得': 'de', '的': 'de', '等': 'deng',
    '地': 'di', '第': 'di', '点': 'dian', '电': 'dian', '调': 'diao', '顶': 'ding', '定': 'ding',
    '东': 'dong', '动': 'dong', '都': 'dou', '读': 'du', '独': 'du', '度': 'du', '端': 'duan',
    '短': 'duan', '段': 'duan', '对': 'dui', '多': 'duo', '朵': 'duo', '额': 'e', '恶': 'e',
    '饿': 'e', '而': 'er', '儿': 'er', '二': 'er', '发': 'fa', '法': 'fa', '反': 'fan',
    '饭': 'fan', '范': 'fan', '方': 'fang', '房': 'fang', '访': 'fang', '放': 'fang', '非': 'fei',
    '费': 'fei', '分': 'fen', '份': 'fen', '风': 'feng', '封': 'feng', '佛': 'fo', '否': 'fou',
    '夫': 'fu', '服': 'fu', '福': 'fu', '父': 'fu', '付': 'fu', '负': 'fu', '附': 'fu',
    '复': 'fu', '该': 'gai', '改': 'gai', '概': 'gai', '干': 'gan', '感': 'gan', '刚': 'gang',
    '高': 'gao', '告': 'gao', '哥': 'ge', '歌': 'ge', '格': 'ge', '个': 'ge', '各': 'ge',
    '给': 'gei', '跟': 'gen', '更': 'geng', '工': 'gong', '公': 'gong', '共': 'gong', '狗': 'gou',
    '构': 'gou', '购': 'gou', '古': 'gu', '股': 'gu', '故': 'gu', '顾': 'gu', '固': 'gu',
    '瓜': 'gua', '挂': 'gua', '关': 'guan', '观': 'guan', '管': 'guan', '馆': 'guan', '光': 'guang',
    '广': 'guang', '规': 'gui', '贵': 'gui', '国': 'guo', '果': 'guo', '过': 'guo', '还': 'hai',
    '孩': 'hai', '海': 'hai', '害': 'hai', '含': 'han', '汉': 'han', '好': 'hao', '号': 'hao',
    '喝': 'he', '和': 'he', '河': 'he', '合': 'he', '何': 'he', '黑': 'hei', '很': 'hen',
    '红': 'hong', '后': 'hou', '候': 'hou', '湖': 'hu', '护': 'hu', '花': 'hua', '华': 'hua',
    '画': 'hua', '话': 'hua', '坏': 'huai', '欢': 'huan', '环': 'huan', '换': 'huan', '黄': 'huang',
    '回': 'hui', '会': 'hui', '婚': 'hun', '活': 'huo', '火': 'huo', '或': 'huo', '机': 'ji',
    '鸡': 'ji', '积': 'ji', '极': 'ji', '急': 'ji', '集': 'ji', '几': 'ji', '己': 'ji',
    '记': 'ji', '计': 'ji', '家': 'jia', '加': 'jia', '假': 'jia', '价': 'jia', '架': 'jia',
    '间': 'jian', '见': 'jian', '建': 'jian', '江': 'jiang', '将': 'jiang', '讲': 'jiang', '交': 'jiao',
    '角': 'jiao', '教': 'jiao', '接': 'jie', '街': 'jie', '节': 'jie', '结': 'jie', '解': 'jie',
    '姐': 'jie', '介': 'jie', '界': 'jie', '今': 'jin', '金': 'jin', '近': 'jin', '进': 'jin',
    '经': 'jing', '京': 'jing', '精': 'jing', '景': 'jing', '警': 'jing', '静': 'jing', '九': 'jiu',
    '久': 'jiu', '酒': 'jiu', '旧': 'jiu', '就': 'jiu', '局': 'ju', '据': 'ju', '句': 'ju',
    '举': 'ju', '具': 'ju', '剧': 'ju', '绝': 'jue', '决': 'jue', '觉': 'jue', '军': 'jun',
    '开': 'kai', '看': 'kan', '康': 'kang', '考': 'kao', '科': 'ke', '可': 'ke', '克': 'ke',
    '刻': 'ke', '客': 'ke', '课': 'ke', '空': 'kong', '口': 'kou', '哭': 'ku', '苦': 'ku',
    '块': 'kuai', '快': 'kuai', '筷': 'kuai', '宽': 'kuan', '款': 'kuan', '况': 'kuang', '亏': 'kui',
    '困': 'kun', '扩': 'kuo', '拉': 'la', '来': 'lai', '蓝': 'lan', '浪': 'lang', '老': 'lao',
    '乐': 'le', '类': 'lei', '冷': 'leng', '离': 'li', '李': 'li', '里': 'li', '理': 'li',
    '力': 'li', '立': 'li', '丽': 'li', '利': 'li', '历': 'li', '例': 'li', '连': 'lian',
    '联': 'lian', '脸': 'lian', '练': 'lian', '恋': 'lian', '凉': 'liang', '两': 'liang', '辆': 'liang',
    '亮': 'liang', '量': 'liang', '料': 'liao', '林': 'lin', '零': 'ling', '领': 'ling', '另': 'ling',
    '留': 'liu', '流': 'liu', '六': 'liu', '楼': 'lou', '路': 'lu', '录': 'lu', '旅': 'lv',
    '绿': 'lv', '乱': 'luan', '论': 'lun', '落': 'luo', '妈': 'ma', '马': 'ma', '买': 'mai',
    '卖': 'mai', '满': 'man', '慢': 'man', '忙': 'mang', '猫': 'mao', '毛': 'mao', '么': 'me',
    '没': 'mei', '每': 'mei', '美': 'mei', '门': 'men', '们': 'men', '梦': 'meng', '米': 'mi',
    '密': 'mi', '秘': 'mi', '免': 'mian', '面': 'mian', '民': 'min', '明': 'ming', '名': 'ming',
    '命': 'ming', '模': 'mo', '末': 'mo', '某': 'mou', '母': 'mu', '目': 'mu', '拿': 'na',
    '那': 'na', '哪': 'na', '奶': 'nai', '男': 'nan', '南': 'nan', '难': 'nan', '脑': 'nao',
    '闹': 'nao', '呢': 'ne', '能': 'neng', '你': 'ni', '年': 'nian', '念': 'nian', '鸟': 'niao',
    '您': 'nin', '牛': 'niu', '农': 'nong', '弄': 'nong', '女': 'nv', '暖': 'nuan', '欧': 'ou',
    '怕': 'pa', '拍': 'pai', '排': 'pai', '牌': 'pai', '派': 'pai', '判': 'pan', '旁': 'pang',
    '跑': 'pao', '朋': 'peng', '批': 'pi', '皮': 'pi', '片': 'pian', '票': 'piao', '品': 'pin',
    '平': 'ping', '评': 'ping', '破': 'po', '普': 'pu', '期': 'qi', '其': 'qi', '奇': 'qi',
    '骑': 'qi', '起': 'qi', '气': 'qi', '汽': 'qi', '七': 'qi', '千': 'qian', '前': 'qian',
    '钱': 'qian', '强': 'qiang', '墙': 'qiang', '桥': 'qiao', '巧': 'qiao', '切': 'qie', '且': 'qie',
    '亲': 'qin', '轻': 'qing', '清': 'qing', '情': 'qing', '请': 'qing', '秋': 'qiu', '求': 'qiu',
    '球': 'qiu', '区': 'qu', '取': 'qu', '去': 'qu', '趣': 'qu', '全': 'quan', '权': 'quan',
    '群': 'qun', '然': 'ran', '让': 'rang', '热': 're', '人': 'ren', '认': 'ren', '任': 'ren',
    '日': 'ri', '容': 'rong', '肉': 'rou', '如': 'ru', '入': 'ru', '软': 'ruan', '瑞': 'rui',
    '润': 'run', '若': 'ruo', '三': 'san', '伞': 'san', '色': 'se', '森': 'sen', '杀': 'sha',
    '沙': 'sha', '山': 'shan', '善': 'shan', '商': 'shang', '上': 'shang', '少': 'shao', '绍': 'shao',
    '社': 'she', '谁': 'shui', '身': 'shen', '深': 'shen', '神': 'shen', '什': 'shen', '生': 'sheng',
    '声': 'sheng', '省': 'sheng', '师': 'shi', '诗': 'shi', '十': 'shi', '时': 'shi', '石': 'shi',
    '实': 'shi', '识': 'shi', '事': 'shi', '是': 'shi', '视': 'shi', '试': 'shi', '收': 'shou',
    '手': 'shou', '首': 'shou', '书': 'shu', '数': 'shu', '水': 'shui', '睡': 'shui', '说': 'shuo',
    '思': 'si', '死': 'si', '四': 'si', '送': 'song', '诉': 'su', '素': 'su', '速': 'su',
    '苏': 'su', '算': 'suan', '虽': 'sui', '随': 'sui', '岁': 'sui', '孙': 'sun', '所': 'suo',
    '他': 'ta', '她': 'ta', '它': 'ta', '台': 'tai', '太': 'tai', '谈': 'tan', '探': 'tan',
    '汤': 'tang', '躺': 'tang', '桃': 'tao', '逃': 'tao', '套': 'tao', '特': 'te', '疼': 'teng',
    '提': 'ti', '题': 'ti', '体': 'ti', '天': 'tian', '听': 'ting', '通': 'tong', '同': 'tong',
    '头': 'tou', '图': 'tu', '土': 'tu', '团': 'tuan', '推': 'tui', '腿': 'tui', '外': 'wai',
    '完': 'wan', '玩': 'wan', '晚': 'wan', '万': 'wan', '王': 'wang', '网': 'wang', '往': 'wang',
    '望': 'wang', '为': 'wei', '位': 'wei', '未': 'wei', '文': 'wen', '问': 'wen', '我': 'wo',
    '无': 'wu', '五': 'wu', '午': 'wu', '物': 'wu', '西': 'xi', '吸': 'xi', '希': 'xi',
    '息': 'xi', '系': 'xi', '喜': 'xi', '下': 'xia', '夏': 'xia', '先': 'xian', '现': 'xian',
    '线': 'xian', '限': 'xian', '香': 'xiang', '想': 'xiang', '向': 'xiang', '像': 'xiang', '小': 'xiao',
    '笑': 'xiao', '校': 'xiao', '效': 'xiao', '些': 'xie', '鞋': 'xie', '写': 'xie', '谢': 'xie',
    '新': 'xin', '心': 'xin', '信': 'xin', '星': 'xing', '行': 'xing', '形': 'xing', '醒': 'xing',
    '姓': 'xing', '兴': 'xing', '休': 'xiu', '修': 'xiu', '需': 'xu', '许': 'xu', '续': 'xu',
    '选': 'xuan', '学': 'xue', '雪': 'xue', '血': 'xue', '寻': 'xun', '训': 'xun', '亚': 'ya',
    '呀': 'ya', '烟': 'yan', '眼': 'yan', '言': 'yan', '研': 'yan', '验': 'yan', '央': 'yang',
    '阳': 'yang', '样': 'yang', '要': 'yao', '药': 'yao', '也': 'ye', '业': 'ye', '夜': 'ye',
    '一': 'yi', '以': 'yi', '亿': 'yi', '已': 'yi', '义': 'yi', '议': 'yi', '因': 'yin',
    '音': 'yin', '印': 'yin', '应': 'ying', '英': 'ying', '影': 'ying', '硬': 'ying', '用': 'yong',
    '有': 'you', '又': 'you', '友': 'you', '右': 'you', '鱼': 'yu', '语': 'yu', '雨': 'yu',
    '玉': 'yu', '元': 'yuan', '员': 'yuan', '原': 'yuan', '院': 'yuan', '远': 'yuan', '愿': 'yuan',
    '月': 'yue', '越': 'yue', '云': 'yun', '运': 'yun', '杂': 'za', '在': 'zai', '再': 'zai',
    '早': 'zao', '造': 'zao', '怎': 'zen', '增': 'zeng', '展': 'zhan', '站': 'zhan', '张': 'zhang',
    '找': 'zhao', '照': 'zhao', '着': 'zhe', '真': 'zhen', '整': 'zheng', '正': 'zheng', '政': 'zheng',
    '之': 'zhi', '知': 'zhi', '直': 'zhi', '值': 'zhi', '职': 'zhi', '只': 'zhi', '纸': 'zhi',
    '指': 'zhi', '至': 'zhi', '制': 'zhi', '质': 'zhi', '治': 'zhi', '中': 'zhong', '钟': 'zhong',
    '种': 'zhong', '重': 'zhong', '周': 'zhou', '州': 'zhou', '洲': 'zhou', '主': 'zhu', '住': 'zhu',
    '助': 'zhu', '注': 'zhu', '专': 'zhuan', '转': 'zhuan', '装': 'zhuang', '准': 'zhun', '资': 'zi',
    '子': 'zi', '自': 'zi', '字': 'zi', '总': 'zong', '走': 'zou', '足': 'zu', '最': 'zui',
    '作': 'zuo', '做': 'zuo', '坐': 'zuo', '座': 'zuo',
    '都': 'du', '检': 'jian', '索': 'suo', '系': 'xi', '统': 'tong', '规': 'gui', '划': 'hua', '局': 'ju',
    '自': 'zi', '然': 'ran', '资': 'zi', '源': 'yuan'
}

def hanzi_to_pinyin(text):
    """将汉字转换为拼音
    
    Args:
        text: 包含汉字的文本
        
    Returns:
        转换后的拼音字符串，不包含声调，小写，无空格
    """
    if not text:
        return ""
        
    result = []
    for char in text:
        # 如果是汉字，查找拼音
        if '\u4e00' <= char <= '\u9fff':
            pinyin = PINYIN_DICT.get(char, char)
            result.append(pinyin)
        else:
            # 如果不是汉字，保留原字符（如字母、数字等）
            # 但只保留字母和数字
            if char.isalnum():
                result.append(char.lower())
    
    # 合并拼音，不加空格
    return ''.join(result)

def is_valid_pinyin_for_name(username, real_name):
    """检查用户名是否为真实姓名的拼音
    
    Args:
        username: 用户输入的用户名
        real_name: 用户输入的真实姓名
        
    Returns:
        bool: 是否符合要求
    """
    try:
        # 将用户名转为小写
        username = username.lower()
        
        # 获取真实姓名的拼音
        name_pinyin = hanzi_to_pinyin(real_name)
        
        # 检查用户名是否与真实姓名的拼音相符
        # 允许用户名是真实姓名拼音的子集（如姓名的首字母等）
        if username == name_pinyin:
            return True, ""
        else:
            return False, f"用户名必须为真实姓名的汉语拼音（小写）: {name_pinyin}"
    except Exception as e:
        logging.error(f"验证用户名拼音失败: {str(e)}")
        return False, "验证用户名失败，请确保用户名为真实姓名的汉语拼音（小写）"
