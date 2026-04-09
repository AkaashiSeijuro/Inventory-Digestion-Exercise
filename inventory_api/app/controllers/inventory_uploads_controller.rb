class InventoryUploadsController < ApplicationController
  def create
    rows = params.permit!.to_h["_json"]

    if !rows.is_a?(Array) || rows.empty?
      render json: { error: "Expected a JSON array" }, status: :unprocessable_entity
      return
    end

    batch_id = SecureRandom.uuid
    now = Time.current

    documents = rows.map do |row|
      raw_properties = row["properties"]
      parsed_properties =
        case raw_properties
        when String
          begin
            JSON.parse(raw_properties)
          rescue JSON::ParserError
            {}
          end
        when Hash
          raw_properties
        else
          {}
        end

      raw_tags = row["tags"]
      parsed_tags =
        case raw_tags
        when String
          raw_tags.split(",").map(&:strip).reject(&:empty?)
        when Array
          raw_tags
        else
          []
        end

      {
        batch_id: batch_id,
        item_num: row["item_num"],
        name: row["name"],
        department: row["department"],
        upc: row["upc"],
        internal_id: row["internal_id"],
        price: row["price"].to_f,
        cost: row["cost"].to_f,
        quantity: row["quantity"].to_i,
        properties: parsed_properties,
        tags: parsed_tags,
        created_at: now,
        updated_at: now
      }
    end

    InventoryUnit.collection.insert_many(documents)

    render json: {
      batch_id: batch_id,
      number_of_units: documents.length
    }, status: :created
  end

  def index
    results = InventoryUnit.collection.aggregate([
      {
        "$group" => {
          "_id" => "$batch_id",
          "number_of_units" => { "$sum" => 1 },
          "average_price" => { "$avg" => "$price" },
          "total_quantity" => { "$sum" => "$quantity" }
        }
      },
      {
        "$project" => {
          "_id" => 0,
          "batch_id" => "$_id",
          "number_of_units" => 1,
          "average_price" => 1,
          "total_quantity" => 1
        }
      },
      {
        "$sort" => { "batch_id" => 1 }
      }
    ]).to_a

    render json: results
  end
end