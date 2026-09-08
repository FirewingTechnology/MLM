from flask import Blueprint
from app.models.package import Package
from app.utils.responses import success_response

packages_bp = Blueprint('packages', __name__, url_prefix='/api/packages')

@packages_bp.route('', methods=['GET'])
def get_packages():
    packages = Package.query.filter_by(is_active=True).all()
    return success_response([p.to_dict() for p in packages])
