from datetime import datetime

class Syringe:
    """分针实体类，表示注射器及其活度信息"""
    
    def __init__(self, id=None, isotope="Ga-68", initial_activity=0.0, 
                 initial_time=None, volume=0.0, device_model=""):
        self.id = id
        self.isotope = isotope
        self.initial_activity = initial_activity
        self.initial_time = initial_time or datetime.now()
        self.volume = volume
        self.device_model = device_model
    
    def to_dict(self):
        return {
            "id": self.id,
            "isotope": self.isotope,
            "initial_activity": self.initial_activity,
            "initial_time": self.initial_time.isoformat() if isinstance(self.initial_time, datetime) else self.initial_time,
            "volume": self.volume,
            "device_model": self.device_model
        }
    
    @classmethod
    def from_dict(cls, data):
        initial_time = data.get("initial_time")
        if isinstance(initial_time, str):
            try:
                initial_time = datetime.fromisoformat(initial_time.replace('Z', '+00:00'))
            except:
                initial_time = datetime.now()
        
        return cls(
            id=data.get("id"),
            isotope=data.get("isotope", "Ga-68"),
            initial_activity=data.get("initial_activity", 0.0),
            initial_time=initial_time,
            volume=data.get("volume", 0.0),
            device_model=data.get("device_model", "")
        ) 