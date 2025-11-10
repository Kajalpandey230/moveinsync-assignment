/**
 * AlertDetailModal Component
 * 
 * Modal displaying full alert details and state history
 */

import { X, AlertCircle, Clock, User, FileText, CheckCircle2 } from 'lucide-react';
import { Alert } from '../services/api';
import { format } from 'date-fns';

interface AlertDetailModalProps {
  alert: Alert | null;
  isOpen: boolean;
  onClose: () => void;
  onResolve?: (alertId: string, notes: string) => Promise<void>;
}

const AlertDetailModal = ({ alert, isOpen, onClose, onResolve }: AlertDetailModalProps) => {
  if (!isOpen || !alert) return null;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'INFO':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'ESCALATED':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'AUTO_CLOSED':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'RESOLVED':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        ></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Alert Details</h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Alert ID and Status */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-mono text-gray-600">{alert.alert_id}</span>
                <div className="flex items-center space-x-2">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getSeverityColor(
                      alert.severity
                    )}`}
                  >
                    {alert.severity}
                  </span>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                      alert.status
                    )}`}
                  >
                    {alert.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Source Type</label>
                <p className="mt-1 text-sm text-gray-900 capitalize">{alert.source_type.toLowerCase()}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Timestamp</label>
                <p className="mt-1 text-sm text-gray-900 flex items-center">
                  <Clock className="h-4 w-4 mr-1 text-gray-400" />
                  {format(new Date(alert.timestamp), 'PPpp')}
                </p>
              </div>
              {alert.metadata.driver_id && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">Driver ID</label>
                  <p className="mt-1 text-sm text-gray-900">{alert.metadata.driver_id}</p>
                </div>
              )}
              {alert.metadata.vehicle_id && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">Vehicle ID</label>
                  <p className="mt-1 text-sm text-gray-900">{alert.metadata.vehicle_id}</p>
                </div>
              )}
            </div>

            {/* Metadata */}
            {Object.keys(alert.metadata).length > 0 && (
              <div className="mb-6">
                <label className="text-xs font-medium text-gray-500 uppercase">Metadata</label>
                <div className="mt-2 bg-gray-50 rounded-lg p-4">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                    {JSON.stringify(alert.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Auto-close reason */}
            {alert.auto_close_reason && (
              <div className="mb-6">
                <label className="text-xs font-medium text-gray-500 uppercase flex items-center">
                  <CheckCircle2 className="h-4 w-4 mr-1 text-green-500" />
                  Auto-Close Reason
                </label>
                <p className="mt-1 text-sm text-gray-900 bg-green-50 p-3 rounded-lg">
                  {alert.auto_close_reason}
                </p>
                {alert.closed_at && (
                  <p className="mt-1 text-xs text-gray-500">
                    Closed at: {format(new Date(alert.closed_at), 'PPpp')}
                  </p>
                )}
              </div>
            )}

            {/* Resolution */}
            {alert.resolved_by && (
              <div className="mb-6">
                <label className="text-xs font-medium text-gray-500 uppercase flex items-center">
                  <User className="h-4 w-4 mr-1 text-gray-400" />
                  Resolution
                </label>
                <p className="mt-1 text-sm text-gray-900">
                  Resolved by: <span className="font-medium">{alert.resolved_by}</span>
                </p>
                {alert.resolution_notes && (
                  <p className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {alert.resolution_notes}
                  </p>
                )}
              </div>
            )}

            {/* State History */}
            {alert.state_history && alert.state_history.length > 0 && (
              <div className="mb-6">
                <label className="text-xs font-medium text-gray-500 uppercase flex items-center mb-3">
                  <FileText className="h-4 w-4 mr-1 text-gray-400" />
                  State History
                </label>
                <div className="space-y-3">
                  {alert.state_history.map((transition, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 rounded-lg p-4 border-l-4 border-blue-500"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          {transition.from_status} → {transition.to_status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {format(new Date(transition.timestamp), 'PPpp')}
                        </span>
                      </div>
                      {transition.triggered_by && (
                        <p className="text-xs text-gray-600">
                          Triggered by: {transition.triggered_by}
                        </p>
                      )}
                      {transition.reason && (
                        <p className="text-xs text-gray-600 mt-1 italic">{transition.reason}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-gray-600 text-base font-medium text-white hover:bg-gray-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertDetailModal;

