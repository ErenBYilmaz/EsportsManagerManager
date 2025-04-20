from typing import Tuple, Dict, List, Any

MessageType = str
Message = Dict
DbName = str
UserName = str
PropertyName = str
ResourceName = str
ResourceAmount = int
CraftingMachineName = str
MessageQueue = List[Tuple[List[UserName], Message, MessageType]]
JSONInfo = Dict[str, Any]
