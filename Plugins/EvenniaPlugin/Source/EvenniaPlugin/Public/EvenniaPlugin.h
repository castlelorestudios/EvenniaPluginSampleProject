// Copyright 1998-2019 Castlelore Studios.

#pragma once

#include "Modules/ModuleManager.h"

class FEvenniaPluginModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
