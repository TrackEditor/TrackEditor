ed -i 's/src\./ /g' src/*py
sed -i 's/from src//g' src/*py
sed -i 's/^ import/import/g' src/*py
sed -i 's/toolbar\.children/#toolbar\.children/g' src/*py
