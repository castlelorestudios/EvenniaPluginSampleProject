// Copyright 1998-2019 Castlelore Studios.

#pragma once
#include "CoreUObject.h"
#include "Engine.h"
#include "Networking.h"
#include "TimerManager.h"

#include "Runtime/JsonUtilities/Public/JsonUtilities.h"
#include "Runtime/JsonUtilities/Public/JsonObjectConverter.h"
#include "Runtime/Json/Public/Dom/JsonObject.h"
#include "Templates/SharedPointer.h"

#include "Kismet/BlueprintFunctionLibrary.h"

#include "EvenniaPluginBPLibrary.generated.h"

UENUM(BlueprintType, Category = "Evennia")
enum class EJsonType : uint8
{
	None	UMETA(DisplayName = "None"),
	Null	UMETA(DisplayName = "Null"),
	String	UMETA(DisplayName = "String"),
	Number	UMETA(DisplayName = "Number"),
	Boolean UMETA(DisplayName = "Boolean"),
	Array	UMETA(DisplayName = "Array"),
	Object	UMETA(DisplayName = "Object")
};

UCLASS(BlueprintType)
class UJSONValue : public UObject
{
	GENERATED_BODY()

public:
	bool IsValid()
	{
		return JSONValue.IsValid();
	}

	TSharedPtr<FJsonValue> JSONValue;
};

UCLASS(BlueprintType)
class UJSONHandle : public UObject
{
	GENERATED_BODY()

public:
	bool IsValid()
	{
		return JSONObject.IsValid();
	}

	TSharedPtr<FJsonObject> JSONObject;
};

UCLASS(BlueprintType)
class UJSONHandleArray : public UObject
{
	GENERATED_BODY()

public:
	TArray<TSharedPtr<FJsonValue>> JSONObjectArray;
};

UCLASS(BlueprintType)
class USocket : public UObject
{
	GENERATED_BODY()

public:
	bool IsValid()
	{
		return (_Socket != nullptr);
	}

	bool SetSocket(FSocket* Socket);
	FSocket* GetSocket();

private:
	FSocket * _Socket;

};


UCLASS()
class UEvenniaPluginBPLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_UCLASS_BODY()

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Connect to a TCP server", Keywords = "Connect TCP Server"), Category = "EvenniaPlugin")
	static USocket* Connect(FString IP, int32 port, bool &success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Send message to the server", Keywords = "TCP Send"), Category = "EvenniaPlugin")
		static bool SendMessage(USocket* Connection, FString Message);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Get message from server", Keywords = "TCP Get"), Category = "EvenniaPlugin")
		static bool GetMessage(USocket* Connection, FString &Message);

	UFUNCTION(BlueprintCallable, BlueprintPure, meta = (DisplayName = "HasPendingData", Keywords = "TCP HasPendingData"), Category = "EvenniaPlugin")
		static bool HasPendingData(USocket* Connection);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "Close connection to TCP server", Keywords = "TCP Close Connection"), Category = "EvenniaPlugin")
		static bool CloseConnection(USocket* Connection);

	/************************************************************************************************************************************************/

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaNewJSONObject", Keywords = "Evennia New JSON Object"), Category = "Evennia")
		static UJSONHandle * EvenniaNewJSONObject();

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaNewJSONValue", Keywords = "Evennia New JSON Value"), Category = "Evennia")
		static UJSONValue * NewJSONValue();

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaNewJSONObjectArray", Keywords = "Evennia New JSON Object Array"), Category = "Evennia")
		static UJSONHandleArray * EvenniaNewJSONObjectArray();

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONElement", Keywords = "Evennia Add JSON Element String"), Category = "Evennia")
		static void EvenniaAddJSONElement(UJSONHandle * JSONHandle, FString Name, FString Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONNumericElement", Keywords = "Evennia Add JSON Numeric Element"), Category = "Evennia")
		static void EvenniaAddJSONNumericElement(UJSONHandle * JSONHandle, FString Name, float Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONObject", Keywords = "Evennia Add JSON Object"), Category = "Evennia")
		static void EvenniaAddJSONObject(UJSONHandle * JSONHandle, FString Name, UJSONHandle * Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONObjectToArray", Keywords = "Evennia Add JSON Object To Array"), Category = "Evennia")
		static void EvenniaAddJSONObjectToArray(UJSONHandleArray * JSONHandleArray, UJSONHandle * Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONArrayToObject", Keywords = "Evennia Add Array to JSON Object"), Category = "Evennia")
		static void EvenniaAddJSONArrayToObject(UJSONHandle * JSONHandle, FString Name, UJSONHandleArray * Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaAddJSONArrayToArray", Keywords = "Evennia Add Array to JSON Array"), Category = "Evennia")
		static void EvenniaAddJSONArrayToArray(UJSONHandleArray * JSONHandleArray, FString Name, UJSONHandleArray * Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONElement", Keywords = "Evennia Get JSON Element"), Category = "Evennia")
		static void EvenniaGetJSONElement(UJSONHandle * JSONHandle, FString Name, FString & Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONNumericElement", Keywords = "Evennia Get JSON Numeric Element"), Category = "Evennia")
		static void EvenniaGetJSONNumericElement(UJSONHandle * JSONHandle, FString Name, float& Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONObject", Keywords = "Evennia Get JSON Object"), Category = "Evennia")
		static UJSONHandle * EvenniaGetJSONObject(UJSONHandle * JSONHandle, FString Name);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONElementMultiple", Keywords = "Evennia Get Multiple JSON Elements from object array"), Category = "Evennia")
		static void EvenniaGetJSONElementMultiple(UJSONHandleArray * JSONHandleArray, int Index, FString Name, FString & Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaSerializeJSONObject", Keywords = "Evennia Serialize JSON Object"), Category = "Evennia")
		static void EvenniaSerializeJSONObject(UJSONHandle * JSONHandle, FString & Value, bool& Success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaSerializeJSONObjectArray", Keywords = "Evennia Serialize JSON Object Array"), Category = "Evennia")
		static void EvenniaSerializeJSONObjectArray(UJSONHandleArray * JSONHandleArray, FString & Value, bool& Success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaParseString", Keywords = "Evennia Parse String"), Category = "Evennia")
		static void EvenniaParseString(UJSONHandle * JSONHandle, FString JSONString, bool& Success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaParseMultiple", Keywords = "Evennia Parse Multiple"), Category = "Evennia")
		static UJSONHandleArray * EvenniaParseMultiple(FString JSONString, int& ElementCount, bool& Success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONObjectFromArray", Keywords = "Evennia Get JSONObject From Array"), Category = "Evennia")
		static UJSONHandle * EvenniaGetJSONObjectFromArray(UJSONHandleArray * JSONHandleArray, int Index, bool& Success);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaPrintJSONArray", Keywords = "Evennia Print a JSONArray"), Category = "Evennia")
		static void EvenniaPrintJSONArray(UJSONHandleArray * JSONHandleArray);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONObjectType", Keywords = "Evennia Get JSON Object Type"), Category = "Evennia")
		static void EvenniaGetJSONObjectType(UJSONHandleArray * JSONHandleArray, int Index, EJsonType & JsonType);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONValueType", Keywords = "Evennia Get JSON Value Type"), Category = "Evennia")
		static void EvenniaGetJSONValueType(UJSONValue * JSONValue, EJsonType & JsonType);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaJSONValueAsObject", Keywords = "Evennia Get JSON Value As Object"), Category = "Evennia")
		static UJSONHandle * EvenniaJSONValueAsObject(UJSONValue * JSONValue);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaJSONValueAsArray", Keywords = "Evennia Get JSON Value as Array"), Category = "Evennia")
		static UJSONHandleArray * EvenniaJSONValueAsArray(UJSONValue * JSONValue);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaJSONValueAsString", Keywords = "Evennia Get JSON Value as String"), Category = "Evennia")
		static void EvenniaJSONValueAsString(UJSONValue * JSONValue, FString& Value);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONArrayHandleAsArray", Keywords = "Evennia Get JSON Array Handle as Array"), Category = "Evennia")
		static void EvenniaGetJSONArrayHandleAsArray(UJSONHandleArray * JSONHandleArray, TArray<UJSONValue*> & JSONValueArray, int& ElementCount);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONObjectKeysAndTypes", Keywords = "Evennia Get JSON Object Keys and Types"), Category = "Evennia")
		static void EvenniaGetJSONObjectKeysAndTypes(UJSONHandle * JSONHandle, TMap<FString, EJsonType> & KeysAndTypes, int& ElementCount);

	UFUNCTION(BlueprintCallable, meta = (DisplayName = "EvenniaGetJSONArrayTypesAndValues", Keywords = "Evennia Get JSON Types and Values"), Category = "Evennia")
		static void EvenniaGetJSONArrayTypesAndValues(UJSONHandleArray * JSONHandleArray, TMap<EJsonType, UJSONValue*> & TypesAndValues, int& ElementCount);

	FTimerHandle fhandle;

private:

	static void EvenniaPrintJSONArray(TArray<TSharedPtr<FJsonValue>> JSONHandleArray, int level);
	static void EvenniaPrintJSONValue(TSharedPtr<FJsonValue> Value, int level);
	static void EvenniaPrintJSONObject(TSharedPtr<FJsonObject> JSONObject, int level);
};







