Rails.application.routes.draw do

  resources :inventory_uploads,
  only:[:create,:index],
  defaults:{format: :json}

end