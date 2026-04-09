class InventoryUnit
  include Mongoid::Document
  include Mongoid::Timestamps

  field :batch_id, type: String
  field :item_num, type: String
  field :name, type: String
  field :department, type: String
  field :upc, type: String
  field :internal_id, type: String
  field :price, type: Float
  field :cost, type: Float
  field :quantity, type: Integer
  field :properties, type: Hash, default: {}
  field :tags, type: Array, default: []

  index({ batch_id: 1 })

  validates :batch_id, presence: true
end