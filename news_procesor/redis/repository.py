import json 
import zlib

from redis import Redis

from news_procesor.redis.redis_client import build_client

class HeadlineRepository():

    def __init__(self) -> None:
        self.redis = build_client()
    
    def _serialize(self, data: dict | list) -> bytes:
        return zlib.compress(json.dumps(data).encode())
    
    def _deserialize(self, payload: bytes) -> dict:
        return json.loads(zlib.decompress(payload))

    def _deserialize_many(self, payloads) -> list[dict]:
        return [self._deserialize(p) for p in payloads]

    def _current_display_headlines_key(self) -> str:
        return "headlines:current_display"
    
    def _new_headlines_key(self) -> str:
        return "headlines:new"
    
    def _current_display_topic_key(self, topic: str) -> str:
        return f"topic:{topic}:current_display"
    
    def _new_topic_key(self, topic: str) -> str:
        return f"topic:{topic}:new"
    
    def _keyword_list_key(self) -> str:
        return f"keywords:list"
    
    def _keyword_data_key(self) -> str:
        return f"keywords:data"
    
    def _keyword_in_progress_key(self) -> str:
        return f"keywords:in_progress"
    
    def _check_headlines_exist(self):
        key = self._new_headlines_key()
        if self.redis.exists(key):
            return
        blank_headlines = self._serialize([])
        self.redis.set(key, blank_headlines)

    def _check_topics_headlines_exist(self, topic: str):
        key = self._new_topic_key(topic)
        if self.redis.exists(key):
            return
        blank_headlines = self._serialize([])
        self.redis.set(key,blank_headlines)

    def shift_current_headlines(self):
        self._check_headlines_exist()

        key = self._current_display_headlines_key()
        headlines = self.retrieve_new_headlines()
        serialized_headlines = self._serialize(headlines)
        self.redis.set(key, serialized_headlines)

    def store_new_headlines(self, headlines: list[dict]):
        key = self._new_headlines_key()
        serialized_headlines = self._serialize(headlines)
        self.redis.set(key, serialized_headlines)

    def retrieve_new_headlines(self):
        key = self._new_headlines_key()
        raw_headlines = self.redis.get(key)
        headlines = self._deserialize(raw_headlines) #type: ignore
        return headlines 

    def retrieve_current_display_headlines(self):
        key = self._current_display_headlines_key()
        raw_headlines = self.redis.get(key)
        headlines = self._deserialize(raw_headlines) #type: ignore
        return headlines 
    
    def shift_current_topic_headlines(self,topic: str):
        self._check_topics_headlines_exist(topic)

        key = self._current_display_topic_key(topic)
        headlines = self.retrieve_new_topic_headlines(topic)
        serialized_headlines = self._serialize(headlines)
        self.redis.set(key, serialized_headlines)

    def store_new_topic_headlines(self, topic:str, headlines: list[dict]):
        key = self._new_topic_key(topic)
        serialized_headlines = self._serialize(headlines)
        self.redis.set(key,serialized_headlines)
    
    def retrieve_new_topic_headlines(self, topic:str):
        key = self._new_topic_key(topic)
        raw_headlines = self.redis.get(key)
        headlines = self._deserialize(raw_headlines) #type: ignore
        return headlines
    
    def retrieve_current_topic_headlines(self, topic:str):
        key = self._current_display_topic_key(topic)
        raw_headlines = self.redis.get(key)
        headlines = self._deserialize(raw_headlines) #type: ignore
        return headlines
    
    def check_for_keyword(self, keyword:str) -> bool:
        active_key = self._keyword_list_key()
        in_progress_key = self._keyword_in_progress_key()
        is_member = self.redis.sismember(active_key,keyword)

        if is_member:
            return True
        else:
            self.redis.sadd(active_key, keyword)
            self.redis.sadd(in_progress_key, keyword)
            return False
        
    def add_keyword_data(self, keyword: str, data: dict):
        key = self._keyword_data_key()
        self.redis.json().set(key,f"$.{keyword}",data)

    def get_task_id_from_keyword(self, keyword: str):
        key = self._keyword_data_key()
        task_id = self.redis.json().get(key,f"$.{keyword}.task_id")[0] #type: ignore
        return task_id

    def retrieve_keyword_data(self, keyword: str):
        key = self._keyword_data_key()
        data = self.redis.json().get(key,f"$.{keyword}")
        if data:
            data = data[0]
            return data
        else:
            return None
        
    def keyword_data_set_status(self, keyword: str, status: str):
        key = self._keyword_data_key()
        self.redis.json().set(key,f"$.{keyword}.status",status)

    def keyword_data_set_show_keyword(self, keyword: str, show_keyword: bool):
        key = self._keyword_data_key()
        self.redis.json().set(key,f"$.{keyword}.show_keyword",show_keyword)

    def keyword_data_set_data(self, keyword: str, data: dict):
        key = self._keyword_data_key()
        self.redis.json().set(key,f"$.{keyword}.show_keyword",data)

    def keyword_data_get_data(self, keyword: str, data: dict):
        key = self._keyword_data_key()
        self.redis.json().get(key,f"$.{keyword}.show_keyword",data)

    def retrieve_in_progress_iterator(self):
        key = self._keyword_in_progress_key()
        return self.redis.sscan_iter(key)
    
    def remove_keyword_from_in_progress(self, keyword: str):
        key = self._keyword_in_progress_key()
        self.redis.srem(key,keyword)
        
