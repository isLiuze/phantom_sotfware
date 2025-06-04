class ActivityPreset:
    """活度预设实体类，用于保存常用的活度设置"""
    
    def __init__(self, name="", isotope="Ga-68", target_activity=0.0, 
                 volume=0.0, device_model="", description=""):
        self.name = name
        self.isotope = isotope
        self.target_activity = target_activity
        self.volume = volume
        self.device_model = device_model
        self.description = description
    
    def to_dict(self):
        return {
            "name": self.name,
            "isotope": self.isotope,
            "target_activity": self.target_activity,
            "volume": self.volume,
            "device_model": self.device_model,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", ""),
            isotope=data.get("isotope", "Ga-68"),
            target_activity=data.get("target_activity", 0.0),
            volume=data.get("volume", 0.0),
            device_model=data.get("device_model", ""),
            description=data.get("description", "")
        ) 