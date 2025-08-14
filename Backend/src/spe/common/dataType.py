from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Type, Optional, Dict, Callable

from spe.common.serialization.serializationMode import SerializationMode
from spe.pipeline.operators.base.dataTypes.window import Window

# DataType name -> DataTypeDefinition
_typeNameDefLookup: Dict[str, DataType.Definition] = dict()

# ValueType name -> DataTypeDefinition
_valueNameDefLookup: Dict[str, DataType.Definition] = dict()

_customDataTypes: List[DataType.Definition] = list()

# TODO: Fuse MonitorDataTypes into this DataTypes


class DataType(ABC):
    class Definition:
        def __init__(self, typeName: str, compositeType: bool = False, systemType: bool = False, primitive: bool = False):
            self.typeName = typeName

            self.systemType = systemType
            self.compositeType = compositeType  # If the type contains multiple values
            self.primitive = primitive

            self._serializer: Dict[SerializationMode, Callable[[Any], Any]] = dict()
            self._deserializer: Dict[SerializationMode, Callable[[Any], Any]] = dict()

        @abstractmethod
        def getValueType(self) -> Type:
            pass

        @abstractmethod
        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            pass

        @abstractmethod
        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            """ Recursively retrieves data type of the data value (and all elements in case of composite types)
            If checkUniformity is true, all composite data elements will be checked to detect uniformity. """

            pass

        def getValueTypeName(self) -> str:
            return self.getValueType().__name__

        # ----------------------------------------------- Serialization ------------------------------------------------

        def registerSerializer(self, targetType: SerializationMode, serializer: Callable[[Any], Any]):
            self._serializer[targetType] = serializer

        def registerDeserializer(self, sourceType: SerializationMode, deserializer: Callable[[Any], Any]):
            self._deserializer[sourceType] = deserializer

        def getSerializer(self, targetMode: SerializationMode):
            return self._serializer.get(targetMode)

        def getDeserializer(self, targetMode: SerializationMode):
            return self._deserializer.get(targetMode)

    def __init__(self, definition: Definition, uniform: Optional[bool] = True):
        self.definition = definition

        # If all elements of a composite types have the same value. None=Unchecked
        # If we have nested composite types the uniform value will only check
        self.uniform = uniform

    @property
    def typeName(self):
        return self.definition.typeName

    def toJSONConfig(self) -> Dict:
        return {"type": self.typeName, "uniform": self.uniform}

    def getNestedTypes(self) -> List[DataType]:
        """ Returns all involved types in this dataType, including the root level type and all nested (composite) types. """
        return [self]

    def isEquals(self, other: DataType):
        return self.typeName == other.typeName

    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    def equals(first: Optional[DataType], second: Optional[DataType]) -> bool:
        """ Checks if this type is equals to another type.
        Nones are considered equal to each other. """

        if first is None and second is None:
            return True
        elif first is None or second is None:
            return False

        return first.isEquals(second)

    @staticmethod
    def fromJSONConfig(data: Dict) -> DataType:
        dType = data["type"]
        uniform = data["uniform"]

        typeDef = DataType.getDefinitionByName(dType)

        return typeDef.fromJSONConfig(data, uniform)

    @staticmethod
    def retrieve(data: Any, checkUniformity: bool = False) -> Optional[DataType]:
        """ Retrieves nested dataType of the input data. """

        typeDef = DataType.retrieveDefinition(data)

        if typeDef is not None:
            return typeDef.fromData(data, checkUniformity)

        return None

    @staticmethod
    def retrieveDefinition(data: Any) -> Optional[DataType.Definition]:
        typeDef = DataType.getDefinitionByValueType(type(data))

        if typeDef is not None:
            return typeDef

        return None

    @staticmethod
    def getDefinitionByName(typeName: str) -> Optional[DataType.Definition]:
        return _typeNameDefLookup.get(typeName, None)

    @staticmethod
    def getDefinitionByValueType(valueType: Type) -> Optional[DataType.Definition]:
        return _valueNameDefLookup.get(valueType.__name__, None)

    @staticmethod
    def getValueTypeName(valueType: Optional[Type]):
        return valueType.__name__ if valueType is not None else None

    @staticmethod
    def register(typeDef: DataType.Definition):
        valType = typeDef.getValueType()
        valTypeName = valType.__name__

        if typeDef.typeName in _typeNameDefLookup or valTypeName in _valueNameDefLookup:
            raise AssertionError(f"DataType {typeDef.typeName} already exists!")

        _typeNameDefLookup[typeDef.typeName] = typeDef
        _valueNameDefLookup[valTypeName] = typeDef

        if not typeDef.systemType:
            _customDataTypes.append(typeDef)

    @staticmethod
    def getCustomTypes() -> List[DataType.Definition]:
        return _customDataTypes


class DictType(DataType):
    name = "Dict"

    class DictDTD(DataType.Definition):
        def __init__(self):
            super().__init__(DictType.name, compositeType=True, systemType=True)

        def getValueType(self) -> Optional[Type]:
            return dict

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            keyType = data["keyType"]
            valType = data["valType"]

            return DictType(self, DataType.fromJSONConfig(keyType) if keyType is not None else None,
                            DataType.fromJSONConfig(valType) if valType is not None else None, uniform)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            # Check all key/value elements to verify uniformity

            if checkUniformity:
                uniform = True
                firstKeyType = None
                firstValType = None

                for k, v in data.items():
                    keyType = DataType.retrieve(k, True)
                    valType = DataType.retrieve(v, True)

                    if firstKeyType is None:
                        firstKeyType = keyType

                    if not DataType.equals(firstKeyType, keyType):
                        uniform = False

                    if firstValType is None:
                        firstValType = valType

                    if not DataType.equals(firstValType, valType):
                        uniform = False

                    if not uniform:  # Not point to check further if already detected violation of uniformity
                        break

                return DictType(self, firstKeyType, firstValType, uniform)

            # Only checks first key/val entry

            else:
                keyType: Optional[DataType] = None
                valType: Optional[DataType] = None

                if len(data) > 0:
                    firstKey, firstVal = next(iter(data.items()))

                    keyType = DataType.retrieve(firstKey)
                    valType = DataType.retrieve(firstVal)

                return DictType(self, keyType, valType, None)

    def __init__(self, definition: Optional[DictDTD] = None, keyType: Optional[DataType] = None, valType: Optional[DataType] = None, uniform: Optional[bool] = False):
        if definition is None:
            definition = DataType.getDefinitionByName(DictType.name)

        super().__init__(definition, uniform=uniform)

        self.keyType = keyType
        self.valType = valType

    def toJSONConfig(self) -> Dict:
        base = super().toJSONConfig()

        base["keyType"] = self.keyType.toJSONConfig() if self.keyType is not None else None
        base["valType"] = self.valType.toJSONConfig() if self.valType is not None else None

        return base

    def getNestedTypes(self) -> List[DataType]:
        res: List[DataType] = [self]

        if self.keyType is not None:
            res.extend(self.keyType.getNestedTypes())

        if self.valType is not None:
            res.extend(self.valType.getNestedTypes())

        return res

    def isEquals(self, other: DictType):
        if not super().isEquals(other):
            return False

        if not DataType.equals(self.keyType, other.keyType):
            return False

        if not DataType.equals(self.valType, other.valType):
            return False

        return True


class WindowType(DataType):
    name = "Window"

    class WindowDTD(DataType.Definition):
        def __init__(self):
            super().__init__(WindowType.name, compositeType=True)

        def getValueType(self) -> Optional[Type]:
            return Window

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            entryType = data["entryType"]

            return WindowType(self, DataType.fromJSONConfig(entryType) if entryType is not None else None, uniform)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            entryType: Optional[DataType] = None
            uniform = True

            if checkUniformity:  # Checks all entries
                for d in data.iterateData():
                    dataType = DataType.retrieve(d, True)

                    if entryType is None:
                        entryType = dataType

                    if not DataType.equals(entryType, entryType):
                        uniform = False

                        break
            elif data.getCount() > 0:  # Only checks first entry
                uniform = None
                entryType = DataType.retrieve(data.getDataAt(0))

            return WindowType(self, entryType, uniform)

    def __init__(self, definition: Optional[WindowDTD] = None, entryType: Optional[DataType] = None, uniform: Optional[bool] = False):
        if definition is None:
            definition = DataType.getDefinitionByName(WindowType.name)

        super().__init__(definition, uniform=uniform)

        self.entryType = entryType

    def toJSONConfig(self) -> Dict:
        base = super().toJSONConfig()

        base["entryType"] = self.entryType.toJSONConfig() if self.entryType is not None else None

        return base

    def getNestedTypes(self) -> List[DataType]:
        res: List[DataType] = [self]

        if self.entryType is not None:
            res.extend(self.entryType.getNestedTypes())

        return res

    def isEquals(self, other: WindowType):
        if not super().isEquals(other):
            return False

        if not DataType.equals(self.entryType, other.entryType):
            return False

        return True


class ArrayType(DataType):
    name = "Array"

    class ArrayDTD(DataType.Definition):
        def __init__(self):
            super().__init__(ArrayType.name, compositeType=True, systemType=True)

        def getValueType(self) -> Optional[Type]:
            return list

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            entryType = data["entryType"]

            return ArrayType(self, DataType.fromJSONConfig(entryType) if entryType is not None else None, uniform)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            entryType: Optional[DataType] = None
            uniform = True

            if checkUniformity:  # Checks all entries
                for d in data:
                    dataType = DataType.retrieve(d, True)

                    if entryType is None:
                        entryType = dataType

                    if not DataType.equals(entryType, dataType):
                        uniform = False

                        break
            elif len(data) > 0:  # Only checks first entry
                uniform = None
                entryType = DataType.retrieve(data[0])

            return ArrayType(self, entryType, uniform)

    def __init__(self, definition: Optional[ArrayDTD] = None, entryType: Optional[DataType] = None, uniform: Optional[bool] = False):
        if definition is None:
            definition = DataType.getDefinitionByName(ArrayType.name)

        super().__init__(definition, uniform=uniform)

        self.entryType = entryType

    def toJSONConfig(self) -> Dict:
        base = super().toJSONConfig()

        base["entryType"] = self.entryType.toJSONConfig() if self.entryType is not None else None

        return base

    def getNestedTypes(self) -> List[DataType]:
        res: List[DataType] = [self]

        if self.entryType is not None:
            res.extend(self.entryType.getNestedTypes())

        return res

    def isEquals(self, other: ArrayType):
        if not super().isEquals(other):
            return False

        if not DataType.equals(self.entryType, other.entryType):
            return False

        return True


class TupleType(DataType):
    name = "Tuple"

    class TupleDTD(DataType.Definition):
        def __init__(self):
            super().__init__(TupleType.name, compositeType=True, systemType=True)

        def getValueType(self) -> Optional[Type]:
            return tuple

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            entryTypeData = data["entryTypes"]

            return TupleType(self, [(DataType.fromJSONConfig(e) if e is not None else None) for e in entryTypeData] if entryTypeData is not None else None, uniform)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            if checkUniformity:
                uniform = True
                firstType: Optional[DataType] = None

                entryTypes = []

                for i in range(len(data)):
                    entryType = DataType.retrieve(data[i], True)
                    entryTypes.append(entryType)

                    if firstType is None:
                        firstType = entryType

                    if not DataType.equals(firstType, entryType):
                        uniform = False

                return TupleType(self, entryTypes, uniform)
            else:
                return TupleType(self, [DataType.retrieve(d) for d in data], None)

    def __init__(self, definition: Optional[TupleDTD] = None, entryTypes: Optional[List[Optional[DataType]]] = None, uniform: Optional[bool] = False):
        if definition is None:
            definition = DataType.getDefinitionByName(TupleType.name)

        super().__init__(definition, uniform=uniform)

        self.entryTypes = entryTypes

    def toJSONConfig(self) -> Dict:
        base = super().toJSONConfig()

        base["entryTypes"] = [(t.toJSONConfig() if t is not None else None) for t in self.entryTypes] if self.entryTypes is not None else None

        return base

    def getNestedTypes(self) -> List[DataType]:
        res: List[DataType] = [self]

        if self.entryTypes is not None:
            for et in self.entryTypes:
                res.extend(et.getNestedTypes())

        return res

    def isEquals(self, other: TupleType):
        if not super().isEquals(other):
            return False

        if self.entryTypes is not None and other.entryTypes is not None:
            for idx, et1 in enumerate(self.entryTypes):
                et2 = other.entryTypes[idx]

                if not DataType.equals(et1, et2):
                    return False

            return True
        else:
            return self.entryTypes == other.entryTypes


class BytesType(DataType):
    name = "Bytes"

    class BytesDTD(DataType.Definition):
        def __init__(self):
            super().__init__(BytesType.name, systemType=True)

        def getValueType(self) -> Optional[Type]:
            return bytes

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return BytesType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return BytesType(self)

    def __init__(self, definition: Optional[BytesDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(BytesType.name)

        super().__init__(definition, uniform=True)


class StringType(DataType):
    name = "String"

    class StringDTD(DataType.Definition):
        def __init__(self):
            super().__init__(StringType.name, systemType=True, primitive=True)

        def getValueType(self) -> Optional[Type]:
            return str

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return StringType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return StringType(self)

    def __init__(self, definition: Optional[StringDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(StringType.name)

        super().__init__(definition, uniform=True)

    @staticmethod
    def create() -> StringType:
        definition = DataType.getDefinitionByName(StringType.name)

        assert isinstance(definition, StringType.StringDTD)

        return StringType(definition)


class IntegerType(DataType):
    name = "Integer"

    class IntegerDTD(DataType.Definition):
        def __init__(self):
            super().__init__(IntegerType.name, systemType=True, primitive=True)

        def getValueType(self) -> Optional[Type]:
            return int

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return IntegerType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return IntegerType(self)

    def __init__(self, definition: Optional[IntegerDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(IntegerType.name)

        super().__init__(definition, uniform=True)


class FloatType(DataType):
    """ Pythons floats are already double precision """

    name = "Float"

    class FloatDTD(DataType.Definition):
        def __init__(self):
            super().__init__(FloatType.name, systemType=True, primitive=True)

        def getValueType(self) -> Optional[Type]:
            return float

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return FloatType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return FloatType(self)

    def __init__(self, definition: Optional[FloatDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(FloatType.name)

        super().__init__(definition, uniform=True)


class BooleanType(DataType):
    name = "Boolean"

    class BooleanDTD(DataType.Definition):
        def __init__(self):
            super().__init__(BooleanType.name, systemType=True, primitive=True)

        def getValueType(self) -> Optional[Type]:
            return bool

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return BooleanType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return BooleanType(self)

    def __init__(self, definition: Optional[BooleanDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(BooleanType.name)

        super().__init__(definition, uniform=True)


class NoneType(DataType):
    name = "None"

    class NoneDTD(DataType.Definition):
        def __init__(self):
            super().__init__(NoneType.name, systemType=True)

        def getValueType(self) -> Optional[Type]:
            return type(None)

        def fromJSONConfig(self, data: Dict, uniform: bool) -> DataType:
            return NoneType(self)

        def fromData(self, data: Any, checkUniformity: bool = False) -> DataType:
            return NoneType(self)

    def __init__(self, definition: Optional[NoneDTD] = None):
        if definition is None:
            definition = DataType.getDefinitionByName(NoneType.name)

        super().__init__(definition, uniform=True)


DataType.register(NoneType.NoneDTD())
DataType.register(BooleanType.BooleanDTD())
DataType.register(FloatType.FloatDTD())
DataType.register(IntegerType.IntegerDTD())
DataType.register(StringType.StringDTD())
DataType.register(BytesType.BytesDTD())
DataType.register(ArrayType.ArrayDTD())
DataType.register(TupleType.TupleDTD())
DataType.register(DictType.DictDTD())
DataType.register(WindowType.WindowDTD())
