// Copyright 1998-2019 Castlelore Studios.

#include "EvenniaPluginBPLibrary.h"
#include "EvenniaPlugin.h"

/**********************************************************************
 *	USocket
 **********************************************************************/
bool USocket::SetSocket(FSocket* Socket)
{
	_Socket = Socket;
	return false;
}

FSocket* USocket::GetSocket()
{
	return _Socket;
}

UEvenniaPluginBPLibrary::UEvenniaPluginBPLibrary(const FObjectInitializer& ObjectInitializer)
: Super(ObjectInitializer)
{

}


USocket* UEvenniaPluginBPLibrary::Connect(FString IP, int32 port, bool& success)
{
	// Create an FSocket pointer to work with and an USocke pointer to return.
	//FSocket* MySockTemp = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateSocket(NAME_Stream, TEXT("Socketer Managed TCP Socket"), false);
	//ISocketSubsystem::GetLocalBindAddr()
	USocket* NetSock = NewObject<USocket>();

	// Create & set a variable to store the parsed ip address
	FIPv4Address ipv4ip;
	FIPv4Address::Parse(IP, ipv4ip);
	//UE_LOG(LogTemp, Warning, TEXT("Connect: FIPv4Address created: %s"), *ipv4ip.ToString());

	// Now combine that with the port to create the address
	//TSharedRef<FInternetAddr> SockAddr = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr(ipv4ip.Value, port);

	TSharedRef<FInternetAddr> addr = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();
	addr->SetIp(ipv4ip.Value);
	addr->SetPort(port);
	//UE_LOG(LogTemp, Warning, TEXT("Connect: FInternetAddr created: %s"), *addr->ToString(true));

	FTcpSocketBuilder builder = FTcpSocketBuilder("SOCKETNAME");
	builder.BoundToAddress(ipv4ip);
	builder.AsBlocking();
	builder.AsReusable();
	int32 backlog = 10;
	//builder.Listening(backlog);

	// ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);


	FSocket* TCPSocket = builder.Build();
	//FSocket* TCPSocket = FTcpSocketBuilder("SOCKETNAME").AsNonBlocking().AsReusable().Listening(1000).Build();

	bool didConnect = false;

	if (TCPSocket != nullptr)
	{
		//UE_LOG(LogTemp, Warning, TEXT("Connect: Socket created! Connecting to server..."));
		didConnect = TCPSocket->Connect(*addr);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("Connect: FTcpSocketBuilder returned null pointer"));
	}

	if (!didConnect)
	{
		UE_LOG(LogTemp, Error, TEXT("Connect: Could not connect to socket"));
		success = false;
		return nullptr;
	}

	NetSock->SetSocket(TCPSocket);

	success = true;
	return NetSock;
}

bool UEvenniaPluginBPLibrary::SendMessage(USocket * Connection, FString Message)
{

	if (!IsValid(Connection))
	{
		UE_LOG(LogTemp, Warning, TEXT("SendMessage: Connection is not valid."));
		return false;
	}

	FSocket* MySocket = Connection->GetSocket();

	if (MySocket == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("SendMessage: GetSocket returned nullptr."));
		return false;
	}

	TCHAR *serializedChar = Message.GetCharArray().GetData();
	if (serializedChar)
	{
		int32 size = FCString::Strlen(serializedChar);
		int32 sent = 0;

		bool successful = MySocket->Send((uint8*)TCHAR_TO_UTF8(serializedChar), size, sent);

		if (!successful)
		{
			UE_LOG(LogTemp, Error, TEXT("SendMessage: Error sending message!!"));
			return false;
		}
		else
		{
			return true;
		}
	}
	return false;
}

bool UEvenniaPluginBPLibrary::GetMessage(USocket* Connection, FString &Message)
{
	if (!IsValid(Connection))
	{
		UE_LOG(LogTemp, Warning, TEXT("GetMessage: Connection is not valid."));
		return false;
	}

	FSocket* MySocket = Connection->GetSocket();

	if (MySocket == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("GetMessage: GetSocket returned nullptr."));
		return false;
	}

	TArray<uint8> BinaryData;
	uint32 Size;

	while (MySocket->HasPendingData(Size))
	{
		BinaryData.Init(0, FMath::Min(Size, 65507u));
		int32 Read = 0;
		MySocket->Recv(BinaryData.GetData(), BinaryData.Num(), Read);
	}

	if (BinaryData.Num() <= 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("GetMessage: No data to read!"));
		return false;
	}
	else
	{
		BinaryData.Add(0);
		//Message = FString(ANSI_TO_TCHAR(reinterpret_cast<const char*>(BinaryData.GetData()))).ReplaceEscapedCharWithChar();
		Message = FString(ANSI_TO_TCHAR(reinterpret_cast<const char*>(BinaryData.GetData())));
		return true;
	}

}

bool UEvenniaPluginBPLibrary::HasPendingData(USocket * Connection)
{
	if (Connection == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("HasPendingData: Connection is a nullptr."));
		return false;
	}

	if (!IsValid(Connection))
	{
		UE_LOG(LogTemp, Warning, TEXT("HasPendingData: Connection is not valid."));
		return false;
	}

	FSocket* MySocket = Connection->GetSocket();

	if (MySocket == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("HasPendingData: GetSocket returned nullptr."));
		return false;
	}

	uint32 Size;

	return MySocket->HasPendingData(Size);
}

bool UEvenniaPluginBPLibrary::CloseConnection(USocket * Connection)
{
	if (Connection == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("HasPendingData: Connection is a nullptr."));
		return false;
	}

	if (!IsValid(Connection))
	{
		UE_LOG(LogTemp, Warning, TEXT("CloseConnection: Connection is not valid."));
		return false;
	}

	FSocket* MySocket = Connection->GetSocket();

	if (MySocket == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("CloseConnection: GetSocket returned nullptr."));
		return false;
	}

	return MySocket->Close();
}

UJSONValue* UEvenniaPluginBPLibrary::NewJSONValue()
{
	UJSONValue* JsonValue = NewObject<UJSONValue>();
	return JsonValue;
}

UJSONHandle* UEvenniaPluginBPLibrary::EvenniaNewJSONObject()
{
	UJSONHandle* JsonHandle = NewObject<UJSONHandle>();
	JsonHandle->JSONObject = MakeShareable(new FJsonObject);
	return JsonHandle;
}

UJSONHandleArray* UEvenniaPluginBPLibrary::EvenniaNewJSONObjectArray()
{
	UJSONHandleArray* JSONHandleArray = NewObject<UJSONHandleArray>();
	return JSONHandleArray;
}

void UEvenniaPluginBPLibrary::EvenniaAddJSONElement(UJSONHandle* JSONHandle, FString Name, FString Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid())
		{
			FString NewName = Name;
			if (NewName != "")
			{
				JSONHandle->JSONObject->SetStringField(NewName, Value);
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONElement: The name of the element must be provided"));
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONElement: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONElement: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaAddJSONNumericElement(UJSONHandle* JSONHandle, FString Name, float Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid())
		{
			FString NewName = Name.ReplaceEscapedCharWithChar();
			JSONHandle->JSONObject->SetNumberField(NewName, (double)Value);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONNumericElement: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONNumericElement: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaAddJSONObject(UJSONHandle* JSONHandle, FString Name, UJSONHandle* Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid() && Value)
		{
			FString NewName = Name.ReplaceEscapedCharWithChar();
			JSONHandle->JSONObject->SetObjectField(Name, Value->JSONObject);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONObject: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONObject: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaAddJSONObjectToArray(UJSONHandleArray* JSONHandleArray, UJSONHandle* Value)
{
	try
	{
		if (JSONHandleArray && Value)
		{
			TSharedRef<FJsonValueObject> JsonValue = MakeShareable(new FJsonValueObject(Value->JSONObject));
			JSONHandleArray->JSONObjectArray.Add(JsonValue);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONObjectToArray: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONObjectToArray: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToObject(UJSONHandle* JSONHandle, FString Name, UJSONHandleArray* Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid() && Value)
		{
			JSONHandle->JSONObject->SetArrayField(Name, Value->JSONObjectArray);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToObject: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToObject: exception caught"));
	}
}



void UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToArray(UJSONHandleArray* JSONHandleArray, FString Name, UJSONHandleArray* Value)
{
	try
	{
		if (JSONHandleArray && Value)
		{
			UJSONHandle* JSONHandle = NewObject<UJSONHandle>();
			UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToObject(JSONHandle, Name, Value);
			TSharedRef<FJsonValueObject> JsonValue = MakeShareable(new FJsonValueObject(JSONHandle->JSONObject));
			JSONHandleArray->JSONObjectArray.Add(JsonValue);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToArray: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaAddJSONArrayToArray: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONElement(UJSONHandle* JSONHandle, FString Name, FString& Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid())
		{
			FString NewName = Name.ReplaceEscapedCharWithChar();
			Value = "";
			JSONHandle->JSONObject->TryGetStringField(NewName, Value);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONElement: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONElement: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONNumericElement(UJSONHandle* JSONHandle, FString Name, float& Value)
{
	try
	{
		if (JSONHandle && JSONHandle->IsValid())
		{
			FString NewName = Name.ReplaceEscapedCharWithChar();
			Value = 0;
			double Temp = 0;
			JSONHandle->JSONObject->TryGetNumberField(NewName, Temp);
			Value = (float)Temp;
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONNumericElement: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONNumericElement: exception caught"));
	}
}


UJSONHandle* UEvenniaPluginBPLibrary::EvenniaGetJSONObject(UJSONHandle* JSONHandle, FString Name)
{
	try
	{
		UJSONHandle* OutHandle = NewObject<UJSONHandle>();
		if (JSONHandle && JSONHandle->IsValid())
		{
			FString NewName = Name.ReplaceEscapedCharWithChar();
			OutHandle->JSONObject = JSONHandle->JSONObject->GetObjectField(NewName);
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONObject: null pointer detected"));
		}
		return OutHandle;
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONObject: exception caught"));
	}
	return nullptr;
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONElementMultiple(UJSONHandleArray* JSONHandleArray, int Index, FString Name, FString& Value)
{
	try
	{
		if (JSONHandleArray)
		{
			Value = "";
			if (Index <= JSONHandleArray->JSONObjectArray.Num() - 1)
			{
				Value = JSONHandleArray->JSONObjectArray[Index]->AsObject()->GetStringField(Name);
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONElementMultiple: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONElementMultiple: exception caught"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaSerializeJSONObject(UJSONHandle* JSONHandle, FString& Value, bool& Success)
{
	if (JSONHandle && JSONHandle->IsValid())
	{
		Value = "";
		Success = false;
		FString OutputString;
		try
		{
			TSharedRef< TJsonWriter<> > Writer = TJsonWriterFactory<>::Create(&OutputString);
			FJsonSerializer::Serialize(JSONHandle->JSONObject.ToSharedRef(), Writer);
			Success = true;
			Value = OutputString;
			return;
		}
		catch (...)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaSerializeJSONObject: Unknown exception caught while serializing object"));
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaSerializeJSONObject: null pointer detected"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaSerializeJSONObjectArray(UJSONHandleArray* JSONHandleArray, FString& Value, bool& Success)
{

	if (JSONHandleArray)
	{
		/*if (JSONHandleArray->JSONObjectArray.Num() > 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaSerializeJSONObjectArray: Array is empty"));
			Value = "";
			Success = false;
			return;
		}*/
		Value = "";
		Success = false;
		FString OutputString;
		try
		{
			TSharedRef< TJsonWriter<> > Writer = TJsonWriterFactory<>::Create(&OutputString);
			FJsonSerializer::Serialize(JSONHandleArray->JSONObjectArray, Writer);

			Success = true;
			Value = OutputString;
			return;
		}
		catch (...)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaSerializeJSONObjectArray: Unknown exception caught while serializing object"));
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaSerializeJSONObjectArray: null pointer detected"));
	}

}

UJSONHandleArray* UEvenniaPluginBPLibrary::EvenniaParseMultiple(FString JSONString, int& ElementCount, bool& Success)
{
	try
	{
		Success = false;
		ElementCount = 0;
		UJSONHandleArray* JSONHandleArray = NewObject<UJSONHandleArray>();

		TSharedRef<TJsonReader<TCHAR>> JsonReader = TJsonReaderFactory<TCHAR>::Create(JSONString);
		if (FJsonSerializer::Deserialize(JsonReader, JSONHandleArray->JSONObjectArray))
		{
			ElementCount = JSONHandleArray->JSONObjectArray.Num();
			Success = true;
		}
		return JSONHandleArray;
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaParseMultiple: Unknown exception caught while parsing string"));
	}
	return nullptr;
}

UJSONHandle* UEvenniaPluginBPLibrary::EvenniaGetJSONObjectFromArray(UJSONHandleArray* JSONHandleArray, int Index, bool& Success)
{
	try
	{
		UJSONHandle* JSONHandle = NewObject<UJSONHandle>();
		if (JSONHandleArray)
		{
			if (Index <= JSONHandleArray->JSONObjectArray.Num())
			{
				Success = true;
				JSONHandle->JSONObject = JSONHandleArray->JSONObjectArray[Index]->AsObject();
				return JSONHandle;
			}
			Success = false;
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONObjectFromArray: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaGetJSONObjectFromArray: exception caught"));
	}
	return nullptr;
}

void UEvenniaPluginBPLibrary::EvenniaParseString(UJSONHandle* JSONHandle, FString JSONString, bool& Success)
{
	Success = false;
	try
	{
		if (JSONHandle && JSONHandle->IsValid())
		{
			TSharedRef<TJsonReader<TCHAR>> JsonReader = TJsonReaderFactory<TCHAR>::Create(JSONString);
			if (FJsonSerializer::Deserialize(JsonReader, JSONHandle->JSONObject))
			{
				Success = true;
				return;
			}
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaParseString: null pointer detected"));
		}
	}
	catch (...)
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaParseString: Unknown exception caught while parsing string"));
	}
}

/***********************************Print JSON Object*************************************/
void UEvenniaPluginBPLibrary::EvenniaPrintJSONArray(UJSONHandleArray* HandleArray)
{
	if (HandleArray)
	{
		UEvenniaPluginBPLibrary::EvenniaPrintJSONArray(HandleArray->JSONObjectArray, 0);
	}
}

void UEvenniaPluginBPLibrary::EvenniaPrintJSONArray(TArray<TSharedPtr<FJsonValue>> JSONValueArray, int level)
{
	if (JSONValueArray.Num() > 0)
	{
		if (level == 0)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::PrintJSONArray: Starting"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::PrintJSONArray: Nested element:"));
		}

		int Num = JSONValueArray.Num();
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Number of elements: %d"), Num);

		for (int x = 0; x < Num; x++)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Printing element number: %d"), x);
			UEvenniaPluginBPLibrary::EvenniaPrintJSONValue(JSONValueArray[x], level);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaParseString: null pointer detected"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaPrintJSONValue(TSharedPtr<FJsonValue> Value, int level)
{
	if (Value && Value.IsValid())
	{
		TArray<TSharedPtr<FJsonValue>> ChildArray;
		FString JsonTypeString;
		EJson JsonType = Value->Type;
		switch (JsonType)
		{
		case EJson::None:
			JsonTypeString = "None";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s."), *JsonTypeString);
			break;

		case EJson::Null:
			JsonTypeString = "Null";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s."), *JsonTypeString);
			break;

		case EJson::String:
			JsonTypeString = "String";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s. Element value: %s"), *JsonTypeString, *Value->AsString());
			break;

		case EJson::Number:
			JsonTypeString = "Number";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element value: %d"), *JsonTypeString, Value->AsNumber());
			break;

		case EJson::Boolean:
			JsonTypeString = "Boolean";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element value: %d"), *JsonTypeString, Value->AsBool() ? "true" : "false");
			break;

		case EJson::Array:
			JsonTypeString = "Array";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s."), *JsonTypeString);
			ChildArray = Value->AsArray();
			UEvenniaPluginBPLibrary::EvenniaPrintJSONArray(ChildArray, level++);
			break;

		case EJson::Object:
			JsonTypeString = "Object";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s."), *JsonTypeString);
			UEvenniaPluginBPLibrary::EvenniaPrintJSONObject(Value->AsObject(), level++);
			break;

		default:
			JsonTypeString = "Undefined";
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::Element type: %s."), *JsonTypeString);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaPrintJSONValue: null pointer detected"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaPrintJSONObject(TSharedPtr<FJsonObject> JSONObject, int level)
{
	if (JSONObject.IsValid())
	{
		TArray<FString> Keys;
		JSONObject->Values.GenerateKeyArray(Keys);

		for (const FString& Key : Keys)
		{
			UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::PrintJSONObject: Processing Key: %s"), *Key);
			const TSharedPtr<FJsonValue>* Field = JSONObject->Values.Find(Key);
			UEvenniaPluginBPLibrary::EvenniaPrintJSONValue(*Field, level);
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UEvenniaPluginBPLibrary::EvenniaPrintJSONObject: null pointer detected"));
	}
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONValueType(UJSONValue* JSONValue, EJsonType& JsonType)
{
	if (JSONValue && JSONValue->IsValid())
	{
		EJson EType = JSONValue->JSONValue->Type;
		EJsonType NewEnum = static_cast<EJsonType>(EType);
		JsonType = NewEnum;
	}
}

UJSONHandle* UEvenniaPluginBPLibrary::EvenniaJSONValueAsObject(UJSONValue* JSONValue)
{
	if (JSONValue && JSONValue->IsValid())
	{
		UJSONHandle* JSONHandle = NewObject<UJSONHandle>();
		JSONHandle->JSONObject = JSONValue->JSONValue->AsObject();
		return JSONHandle;
	}
	return nullptr;
}

UJSONHandleArray* UEvenniaPluginBPLibrary::EvenniaJSONValueAsArray(UJSONValue* JSONValue)
{
	if (JSONValue && JSONValue->IsValid())
	{
		UJSONHandleArray* JSONHandleArray = UEvenniaPluginBPLibrary::EvenniaNewJSONObjectArray();
		JSONHandleArray->JSONObjectArray = JSONValue->JSONValue->AsArray();
		return JSONHandleArray;
	}
	return nullptr;
}

void UEvenniaPluginBPLibrary::EvenniaJSONValueAsString(UJSONValue* JSONValue, FString& Value)
{
	if (JSONValue && JSONValue->IsValid())
	{
		Value = JSONValue->JSONValue->AsString();
	}
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONArrayHandleAsArray(UJSONHandleArray* JSONHandleArray, TArray<UJSONValue*>& JSONValueArray, int& ElementCount)
{
	JSONValueArray.Empty();
	if (JSONHandleArray)
	{
		for (int x = 0; x < JSONHandleArray->JSONObjectArray.Num(); x++)
		{
			UJSONValue* JSONValue = UEvenniaPluginBPLibrary::NewJSONValue();
			JSONValue->JSONValue = JSONHandleArray->JSONObjectArray[x];

			JSONValueArray.Add(JSONValue);
		}
	}

	ElementCount = JSONValueArray.Num();
}


void UEvenniaPluginBPLibrary::EvenniaGetJSONObjectKeysAndTypes(UJSONHandle* JSONHandle, TMap<FString, EJsonType>& KeysAndTypes, int& ElementCount)
{
	KeysAndTypes.Empty();
	ElementCount = 0;
	if (JSONHandle && JSONHandle->IsValid())
	{
		for (auto& Elem : JSONHandle->JSONObject->Values)
		{
			EJson EType = Elem.Value->Type;
			EJsonType NewEnum = static_cast<EJsonType>(EType);
			KeysAndTypes.Add(Elem.Key, NewEnum);
		}
	}

	ElementCount = KeysAndTypes.Num();
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONArrayTypesAndValues(UJSONHandleArray* JSONHandleArray, TMap<EJsonType, UJSONValue*>& TypesAndValues, int& ElementCount)
{
	TypesAndValues.Empty();
	ElementCount = 0;
	if (JSONHandleArray)
	{
		for (int x = 0; x < JSONHandleArray->JSONObjectArray.Num(); x++)
		{
			UJSONValue* JSONValue = UEvenniaPluginBPLibrary::NewJSONValue();
			JSONValue->JSONValue = JSONHandleArray->JSONObjectArray[x];

			EJson EType = JSONHandleArray->JSONObjectArray[x]->Type;
			EJsonType NewEnum = static_cast<EJsonType>(EType);

			TypesAndValues.Add(NewEnum, JSONValue);
		}
	}
	ElementCount = TypesAndValues.Num();
}

void UEvenniaPluginBPLibrary::EvenniaGetJSONObjectType(UJSONHandleArray* JSONHandleArray, int Index, EJsonType& JsonType)
{
	if (JSONHandleArray)
	{
		EJson EType = JSONHandleArray->JSONObjectArray[Index]->Type;
		EJsonType NewEnum = static_cast<EJsonType>(EType);
		JsonType = NewEnum;
	}
}