class RoomSettings:
    def __init__(self):
        self.is_remove_sliderlock: bool = False
        self.is_freemod: bool = False

    @property
    def as_json(self) -> dict[str, bool]:
        return {
            "isRemoveSliderLock": self.is_remove_sliderlock,
            "isFreeMod": self.is_freemod,
        }
