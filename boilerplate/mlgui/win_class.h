
#pragma once
#include "mlgui.2/src/Window.h"

class **WindowClass** : public ml::Window
{
    public : 
        **WindowClass**(ml::App* app);
        **WindowClass**(ml::App* app, ml::Window* parent);
        virtual ~**WindowClass**();

        virtual void init() override;
};
