class HangulComposer:
    CHOSUNG = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 
               'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    JUNGSUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 
                'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
    JONGSUNG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ',
                'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 
                'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    
    # 쌍자음 매핑
    DOUBLE_CONSONANT_MAP = {
        'ㄱ': 'ㄲ',
        'ㄷ': 'ㄸ',
        'ㅂ': 'ㅃ',
        'ㅅ': 'ㅆ',
        'ㅈ': 'ㅉ'
    }
    
    # 겹받침 매핑
    COMPLEX_JONGSUNG_MAP = {
        ('ㄱ', 'ㅅ'): 'ㄳ',
        ('ㄴ', 'ㅈ'): 'ㄵ',
        ('ㄴ', 'ㅎ'): 'ㄶ',
        ('ㄹ', 'ㄱ'): 'ㄺ',
        ('ㄹ', 'ㅁ'): 'ㄻ',
        ('ㄹ', 'ㅂ'): 'ㄼ',
        ('ㄹ', 'ㅅ'): 'ㄽ',
        ('ㄹ', 'ㅌ'): 'ㄾ',
        ('ㄹ', 'ㅍ'): 'ㄿ',
        ('ㄹ', 'ㅎ'): 'ㅀ',
        ('ㅂ', 'ㅅ'): 'ㅄ'
    }
    
    # 복합 모음 매핑 추가
    COMPLEX_VOWEL_MAP = {
        ('ㅗ', 'ㅏ'): 'ㅘ',
        ('ㅗ', 'ㅐ'): 'ㅙ',
        ('ㅗ', 'ㅣ'): 'ㅚ',
        ('ㅜ', 'ㅓ'): 'ㅝ',
        ('ㅜ', 'ㅔ'): 'ㅞ',
        ('ㅜ', 'ㅣ'): 'ㅟ',
        ('ㅡ', 'ㅣ'): 'ㅢ'
    }
    
    # 겹받침을 분해하기 위한 역매핑
    REVERSE_COMPLEX_JONGSUNG = {v: k for k, v in COMPLEX_JONGSUNG_MAP.items()}

    def __init__(self):
        self.reset()
        self.current_text = ""
        self.previous_state = None
        self.last_jamo = None
        self.temp_jong = None

    def reset(self):
        self.cho = None
        self.jung = None
        self.jong = None
        self.last_jamo = None
        self.temp_jong = None

    def try_complex_jongsung(self, current_jong, new_jong):
        if (current_jong, new_jong) in self.COMPLEX_JONGSUNG_MAP:
            return self.COMPLEX_JONGSUNG_MAP[(current_jong, new_jong)]
        return new_jong

    def backspace(self):
        """
        초성, 중성, 종성 순으로 하나씩 삭제
        반환값: (삭제된 후의 현재 조합중인 글자, 변경 여부)
        """
        changed = False
        
        # 현재 조합 중인 글자가 완성된 한글인 경우
        if self.cho and self.jung:
            # 종성이 있으면 먼저 제거
            if self.jong is not None:
                if self.jong in self.REVERSE_COMPLEX_JONGSUNG:
                    cons1, _ = self.REVERSE_COMPLEX_JONGSUNG[self.jong]
                    self.jong = cons1
                else:
                    self.jong = None
                changed = True
            # 중성 제거
            elif self.jung is not None:
                self.jung = None
                changed = True
            # 초성 제거
            elif self.cho is not None:
                self.cho = None
                changed = True
        else:
            # 조합 중이 아닌 경우 전체 초기화
            self.reset()
            changed = True
            
        current = self.combine()
        if current:
            self.current_text = current
        else:
            self.current_text = ""
           
        return self.current_text, changed

    def add_jamo(self, jamo):
        result = None
        
        if jamo in self.CHOSUNG:
            if self.cho is None and self.jung is None:
                self.cho = jamo
            elif self.cho is not None and self.jung is not None:
                if self.jong is None:
                    if jamo in self.JONGSUNG:
                        self.jong = jamo
                    else:
                        result = self.commit()
                        self.cho = jamo
                else:
                    # 겹받침 시도
                    complex_jong = self.try_complex_jongsung(self.jong, jamo)
                    if complex_jong != jamo:  # 겹받침이 가능한 경우
                        self.jong = complex_jong
                    else:  # 겹받침이 불가능한 경우
                        result = self.commit()  
                        self.cho = jamo  # 새 글자 시작
            else:
                result = self.commit()
                self.cho = jamo
            
        elif jamo in self.JUNGSUNG:
            # 복합 모음 처리
            if self.cho is not None and self.jung is not None and not self.jong:
                if (self.jung, jamo) in self.COMPLEX_VOWEL_MAP:
                    self.jung = self.COMPLEX_VOWEL_MAP[(self.jung, jamo)]
                    current = self.combine()
                    if current:
                        self.current_text = current
                    return result, self.current_text
            
            if self.jong is not None:
                # 겹받침 처리
                if self.jong in self.REVERSE_COMPLEX_JONGSUNG:
                    cons1, cons2 = self.REVERSE_COMPLEX_JONGSUNG[self.jong]
                    self.jong = cons1  # 첫 자음은 종성으로
                    result = self.commit()  # 현재 글자 완성
                    self.cho = cons2  # 두번째 자음은 다음 글자의 초성으로
                else:
                    new_cho = self.jong
                    self.jong = None
                    result = self.commit()
                    self.cho = new_cho
                self.jung = jamo
            elif self.cho is not None and self.jung is None:
                self.jung = jamo
            else:
                result = self.commit()
                self.jung = jamo
        
        self.last_jamo = jamo
        current = self.combine()
        
        if current:
            self.current_text = current
            
        return result, self.current_text

    def combine(self):
        if self.cho is not None and self.jung is not None:
            cho_idx = self.CHOSUNG.index(self.cho)
            jung_idx = self.JUNGSUNG.index(self.jung)
            jong_idx = self.JONGSUNG.index(self.jong) if self.jong else 0
            char_code = 0xAC00 + cho_idx * 588 + jung_idx * 28 + jong_idx
            return chr(char_code)
        elif self.cho is not None:
            return self.cho
        elif self.jung is not None:
            return self.jung
        return None

    def commit(self):
        result = self.combine()
        self.reset()
        return result