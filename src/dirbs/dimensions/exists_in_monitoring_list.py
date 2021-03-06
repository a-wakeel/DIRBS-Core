"""
DIRBS dimension function for a IMEIs on the local monitoring list.

Copyright (c) 2018-2020 Qualcomm Technologies, Inc.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted (subject to the
limitations in the disclaimer below) provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this list of conditions and the following
  disclaimer.
- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
  disclaimer in the documentation and/or other materials provided with the distribution.
- Neither the name of Qualcomm Technologies, Inc. nor the names of its contributors may be used to endorse or promote
  products derived from this software without specific prior written permission.
- The origin of this software must not be misrepresented; you must not claim that you wrote the original software.
  If you use this software in a product, an acknowledgment is required by displaying the trademark/log as per the
  details provided here: https://www.qualcomm.com/documents/dirbs-logo-and-brand-guidelines
- Altered source versions must be plainly marked as such, and must not be misrepresented as being the original
  software.
- This notice may not be removed or altered from any source distribution.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY THIS LICENSE. THIS SOFTWARE IS PROVIDED BY
THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from psycopg2 import sql

import dirbs.partition_utils as part_utils
from .base import Dimension


class ExistsInMonitoringList(Dimension):
    """Implementation of exists_in_monitoring_list classification dimension."""

    def __init__(self, *, monitored_days=0, **kwargs):
        """
        Extended Constructor of base.Dimension.

        Arguments:
            monitored_days: for how many number of days an IMEI is in monitoring list
            kwargs: kwargs
        """
        super().__init__(**kwargs)

        try:
            self._monitored_days = int(monitored_days)
        except (TypeError, ValueError):
            raise ValueError("\'monitored_days\' parameter must be an integer, "
                             "got \'{0}\' instead...".format(monitored_days))

    @property
    def algorithm_name(self):
        """Overrides Dimension.algorithm_name."""
        return 'Exists in monitoring list'

    def _matching_imeis_sql(self, conn, app_config, virt_imei_range_start, virt_imei_range_end, curr_date=None):
        """Overrides Dimension._matching_imeis_sql."""
        network_imeis_shard = part_utils.imei_shard_name(base_name='network_imeis',
                                                         virt_imei_range_start=virt_imei_range_start,
                                                         virt_imei_range_end=virt_imei_range_end)
        monitoring_list_shard = part_utils.imei_shard_name(base_name='historic_monitoring_list',
                                                           virt_imei_range_start=virt_imei_range_start,
                                                           virt_imei_range_end=virt_imei_range_end)

        if self._monitored_days > 0:
            interval_sql = sql.SQL("""EXTRACT(DAY FROM NOW() - start_date)""")
            query = sql.SQL("""SELECT imei_norm
                                 FROM {network_imeis_shard}
                                WHERE EXISTS(SELECT imei_norm
                                               FROM {mon_list_shard}
                                              WHERE imei_norm = {network_imeis_shard}.imei_norm
                                                AND EXTRACT(DAY FROM NOW() - start_date)::INT >= {mon_days}
                                                AND end_date IS NULL)""").format(  # noqa: Q449
                network_imeis_shard=sql.Identifier(network_imeis_shard),
                mon_list_shard=sql.Identifier(monitoring_list_shard),
                interval_sql=interval_sql,
                mon_days=sql.Literal(self._monitored_days))
        else:
            query = sql.SQL("""SELECT imei_norm
                                 FROM {network_imeis_shard}
                                WHERE EXISTS(SELECT imei_norm
                                               FROM {mon_list_shard}
                                              WHERE imei_norm = {network_imeis_shard}.imei_norm
                                                AND end_date IS NULL)""").format(  # noqa: Q449
                network_imeis_shard=sql.Identifier(network_imeis_shard),
                mon_list_shard=sql.Identifier(monitoring_list_shard))
        return query.as_string(conn)


dimension = ExistsInMonitoringList
